#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

#ifndef LOG_LIM
#define LOG_LIM 29
#endif

#define N 2

int main(int argc, char **argv)
{
  int64_t i, acc[N], id;

  printf("Computation started\n"); fflush(stdout);

  omp_set_num_threads(N);

  for( i=0; i<N; i++ )
    acc[i] = 7+i;

  #pragma omp parallel
  {
    int64_t a;
    id = omp_get_thread_num();
    a = acc[id];
    for( i=0; i<(1LU<<LOG_LIM); i++ )
    {
      a ^= i*(i<<4);
    }
    acc[id] = a;
  }

  for(i=1; i<N; i++)
    acc[0] ^= acc[i];
  printf("Computation done%c\n", acc[0]?' ':'.');

  return 0;
}
