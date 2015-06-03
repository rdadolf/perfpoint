from nose.plugins.attrib import attr
from perfpoint import *

import numpy as np

sample_counters = [
  (4, '00c0', 'instructions'),
]

@docstring_name
def check_data_shape(data, interval):
  '''Check that align produces any data at all'''
  assert len(data.shape)==2, 'Wrong dimensionality in data'
  assert data.shape[0]>5, 'Insufficient rows in data'
  assert data.shape[1]==len(sample_counters)+1, 'Insufficient columns in data'

@docstring_name
def check_data_values(data, interval):
  '''Check for ridiculous values in the data'''
  assert np.all(data>=0), 'Negative values found in data'
  for (c,counter_tuple) in enumerate(sample_counters):#xrange(1,data.shape[1]+1):
    assert np.count_nonzero(data[:,c+1])>5, 'Mostly zero data found in column '+str(c+1)+': '+str(counter_tuple)

@attr('check','align')
def test_alignment_checks():
  interval = 1000000
  align = Alignment(ipoint_interval=interval, argv=[compute])
  for counter in sample_counters:
    align.add_counter(*counter)
  data = align.run()
  # Run several different diagnostics
  yield (check_data_shape, data, interval)
  yield (check_data_values, data, interval)

@attr('check','align')
@docstring_name
def test_ragged_truncate():
  '''Check that we can truncate ragged arrays'''
  data=[ np.vstack([ np.arange(1,100), np.arange(1,100) ]).T,
         np.vstack([ np.arange(1,200), np.arange(1,200) ]).T ]
  new = align.align_truncated(data,1)
  assert new.shape==(99,3), 'align_truncated didnt truncate correctly'
  assert np.all(new[:,1]==new[:,2]), 'align_truncated didnt align the data'

@attr('check','align')
@docstring_name
def test_ragged_scaled():
  '''Check that we can scale ragged arrays'''
  data=[ np.vstack([ np.arange(1,100), np.arange(1,100) ]).T,
         np.vstack([ np.arange(3,300), np.arange(3,300) ]).T ]
  new = align.align_scaled(data,2)
  assert new.shape==(99,3), 'align_scaled didnt scale correctly'
  assert np.all(new[:,1]==new[:,2]), 'align_scaled didnt align the data'

#@attr('stats')
#def test_alignment_checks():
#  interval = 1000000
# align = Alignment(ipoint_interval=interval, argv=[compute]
#  for counter in sample_counters:
#    align.add_counter(*counter)
#  data = align.run()
#  # Run several different diagnostics
#  yield (check_data, data, interval)
