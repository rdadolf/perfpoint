#include "cli.h"

// FIXME: Move from positional to flags

// Number of position arguments before program & args, not including "-"
void usage(const char *optional_msg){
  if( optional_msg!=NULL )
    printf("%s\n", optional_msg);
  printf("Usage: perfpoint <event-class> <event-config> <event-name> <ipoint-interval> [logfile] - <program> [arg1] ...\n");
  //printf("  Valid event types: hardware: %d, raw: %d, power: %d\n", PERF_TYPE_HARDWARE, PERF_TYPE_RAW, PERF_TYPE_POWER); // FIXME: there are many of these 
}

struct cli_args_t parse_command_line(int argc, char **argv) {
  struct cli_args_t args;
  int i, n_args, cmd_start;
  int POS_ARGS=4;

  // FIXME: strtol error handling
  if( argc<1+POS_ARGS+1+1 ) {
    usage("Not enough arguments");
    exit(-1);
  }

  // FIXME: Actual values is in /sys/bus/event_source/devices/power/type
  args.type = strtol(argv[1], NULL, 10);
  args.config = strtol(argv[2], NULL, 16);
  args.name = strdup(argv[3]);
  args.ipoint_interval = strtol(argv[4], NULL, 10);
  if( args.ipoint_interval<10000 || args.ipoint_interval>(1LU<<44) ) {
    usage("Extreme ipoint interval");
    exit(-1);
  }

  if( strncmp(argv[POS_ARGS+1],"-",2) ) { // Has logfile argument?
    args.logfile = argv[POS_ARGS+1];
    POS_ARGS++;
  } else {
    args.logfile = "perfpoint.log";
  }

  n_args = argc-POS_ARGS-1-1;
  cmd_start = POS_ARGS+1+1;
  if( n_args<=0 ) {
    usage("Missing child process");
    exit(-1);
  }
  args.argc = n_args;
  args.argv = (char **)malloc((1+n_args)*sizeof(char *));
  // We add 1 extra slot and NULL-terminate because execv() is special like that
  for( i=0; i<n_args; i++ )
    args.argv[i] = strdup(argv[cmd_start+i]);
  args.argv[n_args] = NULL;

  #ifdef DEBUG
  printf("user counter:\n  type:%d\n  config:%02lx\n", args.type, args.config);
  printf("user program:\n");
  for( i=0; i<args.argc; i++ )
    printf("  %s\n", args.argv[i]);
  #endif

  return args;
}

