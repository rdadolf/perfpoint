#define _GNU_SOURCE
// Req'd for sigaction(), syscall(), kill(), and some fcntl's
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <assert.h>
#include <errno.h>

#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/fcntl.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <sys/wait.h>

#include "cli.h"

// FIXME: Read the actual value is in /sys/bus/event_source/devices/power/type
// (source: https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-event_source-devices-events)
#define PERF_TYPE_POWER 6

#define GET_UMASK(config) \
  ( (((uint64_t)(config)) & 0xff00LU)>>8 )
#define GET_EVENT(config) \
  ( (((uint64_t)(config)) & 0x00ffLU)    )
#define SET_UMASK(config,umask) \
  ( config = (((uint64_t)(config))    &(~0xff00LU)) \
           | ((((uint64_t)(umask))<<8)&( 0xff00LU)) )
#define SET_EVENT(config,event) \
  ( config = (((uint64_t)(config))    &(~0x00ffLU)) \
           | ((((uint64_t)(event))   )&( 0x00ffLU)) )
#define CONFIG_FROM_EVENT_UMASK(event,umask) \
  ( ((uint64_t)(event)) | (((uint64_t)(umask))<<8) )


static void sig_handler(int signum, siginfo_t *info, void *unused);

/***** Delayed Error Logging **************************************************/
#define MEMLOG_N_ERRORS (1LU<<8)
#define MEMLOG_ERROR_MASK ((MEMLOG_N_ERRORS)-1)
struct memlog_t {
  int errors[MEMLOG_N_ERRORS]; // circular error buffer
  uint64_t error_i; //  Monotonically increasing; only LSBs are used for indexing.
} memlog = {
  .error_i = 0,
};
#define MEMLOG_ERROR() \
  (memlog.errors[ (memlog.error_i++)&MEMLOG_ERROR_MASK ] = __LINE__)
static void memlog_print_errors() {
  uint64_t i;
  if( memlog.error_i>0 )
    printf("\n%lu Errors\n", memlog.error_i);
  for(i=0; i<(memlog.error_i>MEMLOG_N_ERRORS?MEMLOG_N_ERRORS:memlog.error_i); i++)
    printf("  Error on line %d\n", memlog.errors[i]);
}
#define ABORT(msg) { \
  MEMLOG_ERROR(); \
  perror(msg); \
  memlog_print_errors(); \
  exit(-1); \
}

/***** Data structures ********************************************************/

struct child_t { // parent's state about the child
  pid_t pid;
  int fd;
};

#define SZ (1LU<<24)
#define SZ_MASK ((SZ)-1)

struct ipoints_t {
  int fd;
  uint64_t n;  // actual # of ipoints
  uint64_t ipoints[SZ]; // locations of ipoints
};
struct ipoints_t ipoints = {
  .fd = -1, // C99 says everything else is 0.
}; // Must be global so signal handler can update it.

struct samples_t {
  int fd;
  uint64_t n;  // actual # of samples
  uint64_t samples[SZ]; // locations of samples
};
struct samples_t samples = {
  .fd = -1, // C99 says everything else is 0.
}; // Must be global so signal handler can update it. 

static void print_data(const char *filename) {
  uint64_t i;
  FILE *fout;

  if( ipoints.n>SZ ) {
    fprintf(stderr,"[ERROR] Too many samples (%lu>%lu). Data corrupted.\n", ipoints.n, SZ);
    return;
  }

  fout = fopen(filename, "w");
  if( fout==NULL ) {
    fprintf(stderr,"Error: can't open output log. Printing to data to stdout.\n");
    fout=stdout;
  }

  printf("PRINTING %lu DATA POINTS\n", ipoints.n);
  //fprintf("DATA:\n");
  for( i=0; i<ipoints.n; i++ ) {
    fprintf(fout,"%lu,%lu\n", ipoints.ipoints[i], samples.samples[i]);
  }

  fclose(fout);
}

/***** Instruction point wakeup ***********************************************/
struct perf_event_attr ipoint_attr = {
//.type = PERF_TYPE_HARDWARE,
  .type = PERF_TYPE_RAW,
  .size = sizeof(struct perf_event_attr),
//.config = PERF_COUNT_HW_INSTRUCTIONS,
  // cpu/event=0xc0,umask=0x00,name=INST_RETIRED__ANY/
  .config = CONFIG_FROM_EVENT_UMASK(0xc0,0x00),
  .sample_period = 1000000, // Will be replaced
  .sample_type = 0, // No extraneous info
  .read_format = 0, // No extraneous info
  .disabled = 1,
  .inherit = 1,
  .inherit_stat = 1,
  .wakeup_events = 1,
  // Everything else is 0
};

void initialize_ipoints(struct cli_args_t args, struct child_t child) {
  struct sigaction sa;

  ipoint_attr.sample_period = args.ipoint_interval;

  // Set up the signal handler
  memset(&sa, 0, sizeof(struct sigaction));
  sa.sa_sigaction = sig_handler;
  sa.sa_flags = SA_SIGINFO | SA_RESTART;
  assert( sigaction(SIGIO, &sa, NULL)==0 );

  // Set up the perf file descriptor.
#ifdef DEBUG
  printf("Enabling ipoint counter: TYP/EVNT/MASK %u/%lu/%lu\n",
    ipoint_attr.type,
    (uint64_t)(ipoint_attr.config & 0x00ff),
    (uint64_t)((ipoint_attr.config & 0xff00)>>8) );
#endif
  if( (ipoints.fd=syscall(SYS_perf_event_open,&ipoint_attr,child.pid,-1,-1,0))<0 )
    ABORT("Failed to initialize ipoint wakeup event");
  if( 0!=fcntl(ipoints.fd, F_SETFL, O_RDONLY|O_NONBLOCK|O_ASYNC) ) // ASYNC req'd
    ABORT("Failed to set ipoint fd flags");
  if( 0!=fcntl(ipoints.fd, F_SETSIG, SIGIO) ) // Fire a SIGIO on fd ready (wakeup)
    ABORT("Failed to set ipoint signal");
  // F_SETOWN/F_SETOWN_EX control who gets SIGIO signals. F_SETOWN allows you
  // to set a process as a recipient. Linux's special F_SETOWN_EX allows you to
  // set a specific thread. Apparently this allows introspection by a thread
  // which recieves a wakeup event. I think we shouldn't care about this. We're
  // not multithreaded, and we're not interested in recording software-level
  // structures on an interrupt. We just want the counter values, so we only
  // have the parent monitoring signals and taking care of everything.
  //struct f_owner_ex owner;
  //owner.type = F_OWNER_TID;
  //owner.pid = syscall(SYS_gettid);
  //if( 0!=fcntl(ipoints.fd, F_SETOWN_EX, &owner) )
  if( 0!=fcntl(ipoints.fd, F_SETOWN, getpid()) ) // So child doesn't get signal
    ABORT("Failed to set ipoint signal process ownership");
}

/******************************************************************************/
struct perf_event_attr samples_attr = {
  .type = 0xdead, // sentinel, will be replaced with user counter
  .size = sizeof(struct perf_event_attr),
  .config = 0xdead, // sentinel, will be replaced with user counter
  .sample_type = 0, // No extraneous info
  .read_format = 0, // No extraneous info
  .inherit = 1,
  .inherit_stat = 1,
  .disabled = 1,
  // Everything else is 0
};

void initialize_samples(struct cli_args_t args, struct child_t child) {
  // Set the desired event
  samples_attr.type = args.type;
  //samples_attr.config = (((uint16_t)(0xff&args.umask))<<8)|((uint8_t)args.event);
  //samples_attr.config = CONFIG_FROM_EVENT_UMASK(args.event, args.umask);
  samples_attr.config = args.config;

  // Set up the perf file descriptor.
#ifdef DEBUG
  printf("Enabling sample counter: TYP/EVNT/MASK %u/%lu/%lu\n",
    samples_attr.type,
    (uint64_t)(samples_attr.config & 0x00ff),
    (uint64_t)((samples_attr.config & 0xff00)>>8) );
#endif
  // RAPL is different. It can only be measured on cpu0 and it's not core-specific.
  if( samples_attr.type==PERF_TYPE_POWER ) {
    if((samples.fd=syscall(SYS_perf_event_open,&samples_attr,-1,0,-1,0))<0){
      ABORT("Failed to initialize sample wakeup event");
    }
  } else {
    if((samples.fd=syscall(SYS_perf_event_open,&samples_attr,child.pid,-1,-1,0))<0){
      ABORT("Failed to initialize sample wakeup event");
    }
  }
  if( 0!=fcntl(samples.fd, F_SETFL, O_RDONLY|O_NONBLOCK) )
    ABORT("Failed to set user counter fd flags");
}

/***** Child process control **************************************************/

struct child_t start_child( struct cli_args_t args ) {
  int pipefds[2];
  int READ=0, WRITE=1;
  struct child_t child;

  assert( pipe(pipefds)==0 );
  child.pid = fork();
  if( child.pid==0 ) { // child
    close(pipefds[READ]);
    raise(SIGSTOP); // We're ready. Wait for parent signal.
    //printf("GOING\n");
    execvp(args.argv[0], args.argv);
    // Should not return
    perror("Failed to exec child process");
    exit(-1);
  }
  // parent
  close(pipefds[WRITE]);
  child.fd = pipefds[READ];

  // FIXME: wait for child in a more sane way
  usleep(100000);

  return child;
}

void run_child(struct child_t child) {
  kill(child.pid, SIGCONT);
}

/***** Child process control **************************************************/
#if 0
static inline uint64_t get_last_ipoint() {
  // WARNING: This is called in the signal handler. Be aware.
  // Bypass overhead; just reading one word.
  status = syscall(SYS_read, ipoints.fd, &v, sizeof(uint64_t));
  if( status<0 ) {
    MEMLOG_ERROR();
  }
  return v;
}
static inline uint64_t get_last_sample() {
  // WARNING: This is called in the signal handler. Be aware.
  int status;
  uint64_t v;
  // Bypass overhead; just reading one word.
  status = syscall(SYS_read, samples.fd, &v, sizeof(uint64_t));
  if( status<0 ) {
    MEMLOG_ERROR();
  }
  return v;
}
#endif

static void sig_handler(int signum, siginfo_t *info, void *unused) {
  // XXX: super non-reentrant.
  //   Not going to change that. Just make sure that:
  //   (1) we don't get another signal (lol)
  //   (2) the ipoint interval isn't too short (< ~10K and we start losing events)
  int status;
  uint64_t v1=0, v2=0;
  // grab ipoint
  status = syscall(SYS_read, ipoints.fd, &v1, sizeof(uint64_t));
  if( status<0 ) {
    MEMLOG_ERROR();
  }
  ipoints.ipoints[ipoints.n & SZ_MASK] = v1;
  ipoints.n = ipoints.n+1;
  // grab sample
  status = syscall(SYS_read, samples.fd, &v2, sizeof(uint64_t));
  if( status<0 ) {
    MEMLOG_ERROR();
  }
  samples.samples[samples.n & SZ_MASK] = v2;
  samples.n = samples.n+1;
}

/******************************************************************************/
int main(int argc, char **argv) {
  struct cli_args_t args;
  struct child_t child;
  int status;

  args = parse_command_line(argc, argv);
  
  child = start_child(args);

  initialize_ipoints(args, child);
  initialize_samples(args, child);

  if( ioctl(ipoints.fd, PERF_EVENT_IOC_RESET,0)<0 )
    ABORT("Failed to enable ipoints");
  if( ioctl(ipoints.fd, PERF_EVENT_IOC_ENABLE,0)<0 )
    ABORT("Failed to enable ipoints");
  if( ioctl(samples.fd, PERF_EVENT_IOC_ENABLE,0)<0 )
    ABORT("Failed to enable ipoints");

  run_child(child);

  // Wait for child.
  status = waitpid(child.pid, NULL, 0);
  if( status<0 ) {
    perror("waitpid failed");
  }

  memlog_print_errors();

  print_data(args.logfile);

  return 0;
}
