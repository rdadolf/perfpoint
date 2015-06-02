# Module for controlling and parsing perfpoint runs
import subprocess as sub
import tempfile
import os.path
import shutil

testdir = os.path.split(os.path.abspath(__file__))[0]
perfpoint = reduce(os.path.join, [os.path.split(testdir)[0], 'src', 'perfpoint'])
assert os.path.isdir(testdir), 'Couldnt automatically find test directory'
assert os.path.isfile(perfpoint), 'Couldnt automatically find perfpoint binary'

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
  def __init__(self, event_type='4', event_config='00c0', event_name='perfpoint-test-counter', ipoint_interval='1000000', argv=['dd','if=/dev/zero','of=/dev/null','count=100000']):
    self._args = {
      'event_type': str(event_type),
      'event_config': str(event_config),
      'event_name': str(event_name),
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
    self._cmd.append('perfpoint.log')
    self._cmd.append('-')
    self._cmd.extend(self._args['argv'])
    return self._cmd

  def run(self):
    with TestDir() as tmpd:
      os.chdir(tmpd)
      #print '['+tmpd+'] Running "'+' '.join(self._cmd)+'"'
      proc = sub.Popen(self._cmd, stdout=sub.PIPE, stderr=sub.PIPE)
      (self._stdout,self._stderr) = proc.communicate()
      retval = proc.returncode
      assert os.path.isfile('perfpoint.log'), 'No output generated from perfpoint'
      with open('perfpoint.log') as f:
        self._data = f.read()
        return retval

# Decorator that turns the first line of a docstring into the test case name
def docstring_name(func):
  func.description = func.__doc__.split('\n')[0]
  return func
