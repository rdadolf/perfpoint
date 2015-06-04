from nose.plugins.attrib import attr
from perfpoint import *
import sys
import os.path
import numpy as np
from StringIO import StringIO
    
def summarize_distribution(distrib):
  assert len(distrib.shape)==1, 'Bad distribution. Cant summarize.'
  s = u'\u03BC:{mu} \u03C3:{sig} (n={n}) '.format(mu=int(np.mean(distrib)),sig=int(np.std(distrib)), n=distrib.shape[0])
  sys.stdout.write(s)
  sys.stdout.flush()

@docstring_name
def check_data(data,interval):
  '''Sanity check data'''
  assert data.shape[0]!=0, 'No data'
  assert len(data.shape)==2 and data.shape[1]==2, 'Corrupted data'
  assert data.shape[0]>5, 'Insufficient data. Did the program crash?'
  assert np.all(data[:,0]!=0), 'Corrupted data. Null ipoint.'+str(data[:,0])
  assert (np.count_nonzero(data[:,1])-data.shape[0])<5, 'Mostly zero data. Corrupted data.'+str(data[:,1])

@docstring_name
def check_jitter(data,interval):
  '''Check ipoint jitter
Perfpoint sets an interrupt every N instructions. Since the hardware counter is reliable about when it *triggers* the interrupt, the only nondeterminism comes from variable latency in the software stack handling it. We can measure that by comparing the number of instructions between recorded ipoints and the desired interval.
'''
  ipoints = data[:,0]
  jitter = (ipoints[1:] - ipoints[:-1])-interval
  summarize_distribution(jitter)
  assert np.mean(jitter)<(interval*.01), 'Excessive jitter'

@docstring_name
def check_drift(data,interval):
  '''Check ipoint drift
We ask perf_events to signal us every N instructions, but that wakeup has overhead in both the signalling, perf_event bookkeeping, and context switching. This is an estimate for that, and normally, it should be strictly positive. (If it isn't, it implies that we were woken up *before* the counter interrupt, and something is probably broken.)
'''
  expected = np.arange(1,data.shape[0]+1)*interval
  ipoints = data[:,0]
  drift = ipoints-expected
  summarize_distribution(drift)
  assert np.all(drift>0), 'Drift is negative. Something is probably wrong with the signaling.'
  assert np.mean(drift)<100000, 'Excessive drift'

@docstring_name
def check_skew(data,interval):
  '''Check ipoint/counter skew
Perfpoint triggers an interrupt read every N instructions and then reads both
the instruction counter and the user counter. Even though we tacitly assume
that these two counters are read "at the same time", there is nonzero latency
between them. By reading the instruction counter twice, we can get an estimate
of that latency, measured in instructions.
'''
  skew = data[:,1]-data[:,0]
  summarize_distribution(skew)
  assert np.all(skew>0), 'Skew is negative.'+str(np.nonzero(skew>0)[0])
  assert np.mean(skew)<10000, 'Excessive skew'

@attr('stats')
def test_ipoint_stability():
  interval = 1000000
  pp = PerfPoint(ipoint_interval=interval,argv=[compute])
  pp.run()
  data = np.loadtxt(StringIO(pp.data),delimiter=',')
  # Run several different diagnostics
  yield (check_data,data,interval)
  yield (check_jitter,data,interval)
  yield (check_drift,data,interval)
  yield (check_skew,data,interval)

