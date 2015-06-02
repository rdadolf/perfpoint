from nose.plugins.attrib import attr

from perfpoint import *

@attr('check')
@docstring_name
def test_executable():
  '''Check whether perfpoint exists'''
  pp = PerfPoint()
  retval = pp.run()
  assert retval==0, 'Perfpoint exited with error code '+str(retval)


