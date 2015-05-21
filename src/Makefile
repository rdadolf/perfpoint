################################################################################
CC=clang
LDFLAGS=-static
# Be verbose and picky when developing
DEBUG_CFLAGS=-g -Wall -Werror -std=c99 -DDEBUG
# Be fast and loose when releasing
RELEASE_CFLAGS=-O3 -Wall -std=c99

################################################################################
.PHONY: default release new-release debug new-debug clean
default: release

perfpoint: perfpoint.c cli.c cli.h
	$(CC) $(CFLAGS) -o perfpoint perfpoint.c cli.c

# RELEASE
release: CFLAGS=$(RELEASE_CFLAGS)
release: perfpoint
new-release: clean release

# DEBUG
debug: CFLAGS=$(DEBUG_CFLAGS)
debug: perfpoint
new-debug: clean debug

# CLEAN UP
clean:
	rm -f perfpoint
