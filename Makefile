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
