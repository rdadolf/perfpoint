#define _GNU_SOURCE
// Req'd for strdup()
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <linux/perf_event.h>

struct cli_args_t {
  // user counter
  unsigned int type; // PERF_TYPE_*
  uint64_t config; 
  char *name;
  uint64_t ipoint_interval;
  // output
  char *logfile;
  // user program
  int argc;
  char **argv;
};

void usage(const char *optional_msg);
struct cli_args_t parse_command_line(int argc, char **argv);
