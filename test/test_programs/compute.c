#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

#ifndef LOG_LIM
#define LOG_LIM 30
#endif

int main(int argc, char **argv)
{
  int64_t i, acc;

  printf("Computation started\n"); fflush(stdout);
  acc = 7;
  for( i=0; i<(1LU<<LOG_LIM); i++ )
  {
    acc ^= i*(i<<4);
  }
  printf("Computation done%c\n", acc?' ':'.');
  return 0;
}
