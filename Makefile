.PHONY: release new-release debug new-debug clean

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

test: checktest statstest

checktest: release
	nosetests -vsa 'check'
statstest: release
	nosetests -vsa 'stats'
