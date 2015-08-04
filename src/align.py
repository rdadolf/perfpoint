#!/usr/bin/env python

import numpy as np
import argparse


def load_traces(files):
  return [np.loadtxt(f, delimiter=',') for f in files]

def align_truncated(traces, interval_s):
  '''Aligns a set of traces, truncating longer samples.
  The assumption on determinism here is that runtime variance is negligible.'''
  interval = int(interval_s)
  min_n = min([t.shape[0] for t in traces])
  ipoints = np.arange(1,min_n+1)*interval # desired ipoints
  data = np.empty((min_n, len(traces)+1))
  data[:,0] = ipoints
  for (c,t) in enumerate(traces):
    data[:,c+1] = np.interp(data[:,0], t[:,0], t[:,1], left=0.)
  return data

def align_scaled(traces, interval_s):
  '''Aligns a set of traces, scaling them all to the same length first.
  The assumption on determinism here is that runtime variance is a constant
  environmental factor.'''
  interval = int(interval_s)
  mean_maxpoint = np.mean([t[-1] for t in traces])
  #print 'mean maxpoint',mean_maxpoint
  last_desired_ipoint = np.floor(mean_maxpoint/interval)*interval
  ipoints = np.arange(interval,last_desired_ipoint+1,interval)
  #print 'last desired',last_desired_ipoint
  data = np.empty((ipoints.shape[0], len(traces)+1))
  data[:,0] = ipoints
  for (c,t) in enumerate(traces):
    scaling_factor = last_desired_ipoint/t[-1,0]
    #print scaling_factor,type(scaling_factor)
    scaled_t = t * scaling_factor
    #print np.abs(scaled_t[-1,0]-last_desired_ipoint)
    assert np.abs(scaled_t[-1,0]-last_desired_ipoint)<1.0, 'bad scaling'
    data[:,c+1] = np.interp(data[:,0], scaled_t[:,0], scaled_t[:,1], left=0.)
  return data

def correct_for_oversampling(trace):
  '''Smooth out spikes due to oversampling.
  While most hardware counters update faster than we can sample, a few (RAPL) do not. When we sample these at reasonably high frequencies, the cumulative value ends up being identical for several samples. This causes artifacts for analysis and regression downstream. To fix it, we simply make a local linear approximation and smooth out the spike over the samples which were repeated.
  '''
  n_repeats = 0
  last_good_sample = 0.
  for row in xrange(1,trace.shape[0]):
    if trace[row,1]==trace[row-1,1]: # Found a repeat
      if n_repeats==0:  # First repeat
        last_good_sample = trace[row-1,1]
      n_repeats += 1
    elif n_repeats!=0: # First non-repeat after a repeat sequence
      first_new_sample = trace[row,1]
      # Go back and fix everything up
      for nth,idx in zip(xrange(1,n_repeats+1), xrange(row-n_repeats,row)):
        # Add the correction factor
        trace[idx,1] += (first_new_sample-last_good_sample)*nth/(n_repeats+1)
      n_repeats = 0
    else: # Not a repeat, not after a repeat
      n_repeats = 0
  # Note: the last repeat sequence will not be fixed. Deal with it. *shrug*
  return trace

def cumul2delta(cumul):
  '''Changes cumulative counters into deltas'''
  delta = np.copy(cumul)
  delta[1:,:] -= delta[:-1,:]
  return delta


if __name__=='__main__':
  cli = argparse.ArgumentParser()
  cli.add_argument('files', metavar='tracefile', nargs='+', help='A perfpoint tracefile')
  cli.add_argument('-i', '--interval', default=1000000, help='The ipoint interval used in the perfpoint traces')
  g = cli.add_mutually_exclusive_group()
  g.add_argument('--truncated', action='store_true', default=False, help='Fix longer traces by truncating rather than scaling')
  g.add_argument('--scaled', action='store_true', default=True, help='Fix longer traces by truncating rather than scaling')
  cli.add_argument('--no-oversample-correction', action='store_true', default=False, help='Disable automatic smoothing of stairstep samples caused by oversampling. This is generally harmless, even if you dont have oversampled counters.')
  cli.add_argument('-o','--output', default='aligned.out', help='Name of the file to save aligned traces into')
  args = cli.parse_args()

  assert len(args.files)>1, 'Must have more than one tracefile to align anything'

  with open(args.output,'w') as f:
    traces = load_traces(args.files)

    if not args.no_oversample_correction:
      traces = map(correct_for_oversampling, traces)

    if args.truncated:
      data = align_scaled(traces, args.interval)
    else:
      data = align_truncated(traces, args.interval)

    np.savetxt(f, data, delimiter=',', fmt='%.2f')
