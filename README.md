[![build status](https://api.travis-ci.org/rdadolf/perfpoint.svg?branch=master)](https://travis-ci.org/rdadolf/perfpoint)

## What is perfpoint and should I use it?

Perfpoint samples hardware counters at regular intervals, and it depends.

If you're just looking for a way to read hardware performance counters, probably not. Linux's [perf](https://perf.wiki.kernel.org/index.php/Main_Page) tool already does that reasonably well. The documentation is somewhat sparse, but it likely does what you want.

Perfpoint solves a slightly more specific problem which perf has problems with: triggering hardware counters reads every *n* instructions. Actually, perf *can* handle this in some situations using something called counter groups. Unfortunately, counter groups suffer from some restrictions on when and how you can use them, including disallowing sampling from different PMUs. Perfpoint is effectively a manual workaround for this. It triggers interrupts using a free-running instruction counter and records another arbitrary counter on wakeup. The end result is a set of performance counter samples at regular, user-specified intervals.

## What's included?

The primary tool is `perfpoint`, a command-line tool that lets you read a hardware counter every *n* instructions. Run it without any options to get usage. Note: you'll really need to understand some of the details of how Linux's perf interface works to use it, since specifying a harware counter requires some arcane knowledge.

In addition, perfpoint comes with postprocessing scripts to clean up the sample data it produces. For instance, in modern processors, you can't keep track of more than a handful of counters, and one common hack is to run your program several times and record different counters every time. Because programs aren't completely deterministic, this adds artifacts to the data. The `align.py` script attempts to clean up some of this noise. Again, run the program without arguments to get usage.
