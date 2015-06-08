#include "cli.h"

const struct option long_options[] = {
  {.name="help", .has_arg=no_argument, .flag=NULL, .val='h'},
  {.name="event-type", .has_arg=required_argument, .flag=NULL, .val='t'},
  {.name="event-config", .has_arg=required_argument, .flag=NULL, .val='c'},
  {.name="event-name", .has_arg=required_argument, .flag=NULL, .val='n'},
  {.name="logfile", .has_arg=required_argument, .flag=NULL, .val='f'},
  {.name="interval", .has_arg=required_argument, .flag=NULL, .val='i'},
  {0,0,0,0}
};
const char *short_options = "ht:c:n:f:i:";

// Number of position arguments before program & args, not including "-"
void usage(const char *optional_msg){
  const struct option *o;
  if( optional_msg!=NULL )
    printf("%s\n", optional_msg);
  printf("Usage: perfpoint <flags> -- <program> [arg1] ...\n");
  for( o=&long_options[0]; !(o->name==0&&o->has_arg==0&&o->flag==0&&o->val==0); o++ ) {
    printf("\t-%c --%s%s\n", o->val, o->name, (o->has_arg!=no_argument) ? "=<value>":"");
  }
}

struct cli_args_t parse_command_line(int argc, char **argv) {
  struct cli_args_t args;
  int opt;

  memset(&args, 0, sizeof(struct cli_args_t));

  // Defaults
  args.logfile = "perfpoint.log";
  args.ipoint_interval = 1000000;
  args.type = 4;
  args.config = 0x00c0;
  args.name = "INSTRUCTION_RETIRED";

  while(1) {
    int idx, i;

    opt = getopt_long(argc, argv, short_options, long_options, &idx);

    switch(opt) {
      case 't':
        args.type = strtol(optarg, NULL, 10);
        //printf("Set type %u\n", args.type);
        break;
      case 'c':
        args.config = strtol(optarg, NULL, 16);
        //printf("Set config %lu\n", args.config);
        break;
      case 'n':
        args.name = strdup(optarg);
        //printf("Set name %s\n", args.name);
        break;
      case 'i':
        args.ipoint_interval = strtol(optarg, NULL, 10);
        //printf("Set interval %lu\n", args.ipoint_interval);
        break;
      case 'f':
        args.logfile = strdup(optarg);
        //printf("Set logfile %s\n", args.logfile);
        break;
      case 'h':
        usage(NULL);
        exit(0);
      case -1:
        if( optind==argc ) {
          usage("No user program specified");
          exit(-1);
        }
        args.argc = 0;
        args.argv = (char **)malloc((argc-optind+1)*sizeof(char*));
        for( i=0; optind<argc; i++,optind++ ) {
          args.argv[args.argc] = strdup(argv[optind]);
          args.argc++;
        }
        args.argv[args.argc] = NULL;
        return args;
      default:
        usage(NULL);
        exit(-1);
    }
  }
  // Nobody falls through the infinite loop
}
