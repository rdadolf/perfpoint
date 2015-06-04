# perfpoint
[![build status](https://api.travis-ci.org/rdadolf/perfpoint.svg?branch=master)](https://travis-ci.org/rdadolf/perfpoint)

Flexible performance counter sampling

----

### What's included?

The primary tool is `perfpoint`, a command-line tool that lets you read a hardware counter every *n* instructions. Run it without any options to get usage. Note: you'll really need to understand some of the details of how Linux's perf interface works to use it, since specifying a harware counter requires some arcane knowledge.

Due to hardware limitations, you can't keep track of more than a handful of counters. One solution is to assume determinism and run your program several times, recording different counters every time. Because programs *aren't* completely deterministic, we have to do some clean-up afterwards. The `align.py` script takes care of this. Again, run the program without arguments to get usage.
