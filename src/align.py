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
    assert np.abs(scaled_t[-1,0]-last_desired_ipoint)<0.0001, 'bad scaling'
    data[:,c+1] = np.interp(data[:,0], scaled_t[:,0], scaled_t[:,1], left=0.)
  return data

def cum2delta(cum):
  '''Changes cumulative counters into deltas'''
  delta = np.copy(cum)
  delta[1:,:] -= delta[:-1,:]
  return delta


if __name__=='__main__':
  cli = argparse.ArgumentParser()
  cli.add_argument('files', metavar='tracefile', nargs='+', help='A perfpoint tracefile')
  cli.add_argument('-i', '--interval', default=1000000, help='The ipoint interval used in the perfpoint traces')
  cli.add_argument('--truncated', action='store_true', default=False, help='Fix longer traces by truncating rather than scaling')
  args = cli.parse_args()

  assert len(args.files)>1, 'Must have more than one tracefile to align anything'

  with open('aligned.out','w') as f:
    if args.truncated:
      data = align_scaled(load_traces(args.files), args.interval)
    else:
      data = align_truncated(load_traces(args.files), args.interval)
    np.savetxt(f, data, delimiter=',', fmt='%.2f')
