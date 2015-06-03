# Module for controlling and parsing perfpoint runs
import subprocess as sub
import tempfile
import os.path
import shutil
import sys

testdir = os.path.split(os.path.abspath(__file__))[0]
assert os.path.isdir(testdir), 'Couldnt automatically find test directory'
perfpoint = reduce(os.path.join, [os.path.split(testdir)[0], 'src', 'perfpoint'])
assert os.path.isfile(perfpoint), 'Couldnt automatically find perfpoint binary'
sys.path.append( os.path.join(os.path.split(testdir)[0], 'src') )

import align

compute = reduce(os.path.join, [testdir, 'test_programs', 'compute'])

class TestDir:
  def __init__(self):
    self._d = '/tmp/INVALID_TEST_DIRECTORY_PATH'
  def __enter__(self):
    self._d = tempfile.mkdtemp(prefix='perfpoint_test_')
    assert self._d is not None, 'Failed to create temporary directory'
    assert self._d==os.path.abspath(self._d), 'Invalid temporary directory path'
    assert os.path.isdir(self._d), 'Failed to create temporary directory'
    return self._d
  def __exit__(self, exception_type, exception, traceback):
    shutil.rmtree(self._d)

class PerfPoint:
  def __init__(self, event_type='4', event_config='00c0', event_name='perfpoint-test-counter', logfile='perfpoint.log', ipoint_interval='1000000', argv=['dd','if=/dev/zero','of=/dev/null','count=100000']):
    self._args = {
      'event_type': str(event_type),
      'event_config': str(event_config),
      'event_name': str(event_name),
      'logfile': str(logfile),
      'ipoint_interval': str(ipoint_interval),
      'argv': argv
    }
    self._validate_cli()
    self._stdout = ''
    self._stderr = ''
    self._data = ''

  @property
  def stdout(self):
    return self._stdout
  @property
  def stderr(self):
    return self._stderr
  @property
  def data(self):
    return self._data

  def _validate_cli(self):
    evtype = int(self._args['event_type'])
    assert evtype>0 and evtype<100, 'Invalid event type passed to perfpoint'
    assert self._args['event_config'].isalnum(), 'Invalid event configuration passed to perfpoint'
    ipoint = int(self._args['ipoint_interval'])
    assert ipoint>=10000 and ipoint<=(1<<44), 'Invalid ipoint interval passed to perfpoint'
    assert type(self._args['argv']) is list, 'Perfpoint program-under-test must be specified as a list'
    self._cmd = [perfpoint]
    self._cmd.extend( map(lambda k: self._args[k], ['event_type', 'event_config', 'event_name','ipoint_interval']) )
    self._cmd.append(self._args['logfile'])
    self._cmd.append('-')
    self._cmd.extend(self._args['argv'])
    return self._cmd

  def _run(self):
    #print 'Running "'+' '.join(self._cmd)+'"'
    proc = sub.Popen(self._cmd, stdout=sub.PIPE, stderr=sub.PIPE)
    (self._stdout,self._stderr) = proc.communicate()
    return proc.returncode

  def run(self):
    with TestDir() as tmpd:
      os.chdir(tmpd)
      retval = self._run()
      assert os.path.isfile('perfpoint.log'), 'No output generated from perfpoint'
      with open('perfpoint.log') as f:
        self._data = f.read()
        return retval

class Alignment:
  def __init__(self, ipoint_interval, argv=['dd','if=/dev/zero','of=/dev/null','count=100000']):
    self._ipoint_interval = str(ipoint_interval)
    self._argv = argv
    self._counters = [] # [ (evtype,evconf,evname), ... ]

  def add_counter(self, event_type, event_config, event_name):
    self._counters.append( (event_type, event_config, event_name) )

  def run(self, scaled=True, smooth=True):
    with TestDir() as tmpd:
      os.chdir(tmpd)
      logfiles=[]
      for (evtype,evconf,evname) in self._counters:
        logfile = 'LOG_'+str(evname)
        logfiles.append(logfile)
        pp = PerfPoint( event_type = evtype, 
                        event_config = evconf,
                        event_name = evname,
                        logfile = logfile,
                        ipoint_interval = self._ipoint_interval,
                        argv = self._argv )
        assert pp._run()==0, 'Failed perfpoint run for counter '+str((evtype,evconf,evname))
        assert os.path.isfile(logfile), 'No perfpoint output for counter '+str((evtype,evconf,evname))
      # Now align it
      traces = align.load_traces(logfiles)
      if smooth:
        traces = map(align.correct_for_oversampling, traces)
      if scaled:
        data = align.align_scaled(traces, self._ipoint_interval)
      else:
        data = align.align_truncated(traces, self._ipoint_interval)
      return data

# Decorator that turns the first line of a docstring into the test case name
def docstring_name(func):
  assert hasattr(func,'__doc__'), 'No docstring in function "'+str(func)+'"'
  assert func.__doc__ is not None, 'No docstring in function "'+str(func)+'"'
  assert len(func.__doc__)>0, 'No docstring in function "'+str(func)+'"'
  func.description = func.__doc__.split('\n')[0]
  return func
