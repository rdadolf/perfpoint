CC=clang
LDFLAGS=-static
CFLAGS=-O3 -std=c99

BIN=short compute ompcompute javacompute.jar

all: $(BIN)

short: compute.c
	$(CC) $(CFLAGS) -DLOG_LIM=25 compute.c $(LDFLAGS) -o short

ompcompute: ompcompute.c
	gcc $(CFLAGS) -fopenmp ompcompute.c $(LDFLAGS) -o ompcompute

javacompute.jar: javacompute.class
	jar cfe javacompute.jar javacompute javacompute.class
javacompute.class: javacompute.java
	javac javacompute.java

# everything else is implicit

clean:
	rm -f $(BIN) javacompute.class
