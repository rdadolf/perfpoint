.PHONY: release new-release debug new-debug test_programs test checktest statstest clean

default: release

release:
	@$(MAKE) -C src $@
new-release:
	@$(MAKE) -C src $@
debug:
	@$(MAKE) -C src $@
new-debug:
	@$(MAKE) -C src $@
clean:
	@$(MAKE) -C src $@

test_programs:
	@$(MAKE) -C test/test_programs

test: checktest statstest

checktest: release test_programs
	nosetests -vsa 'check'
statstest: release test_programs
	nosetests -vsa 'stats'
