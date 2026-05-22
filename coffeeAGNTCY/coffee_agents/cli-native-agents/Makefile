# CLI-native agents helper targets.
#
# Usage:
#   make install
#   make install AGENT=claude-code
#   make install AGENT=codex
#   make install AGENT=opencode
#   make install AGENT=copilot-cli SKILL_ROOT=.copilot/skills
#   make clean

AGENT ?=
SKILL_ROOT ?=
VERBOSE ?= 0
AGENT_ARG := $(if $(AGENT),$(AGENT),)
INSTALL_FLAGS := $(if $(SKILL_ROOT),--skill-root $(SKILL_ROOT),)
VERBOSE_FLAG := $(if $(filter 1 true yes,$(VERBOSE)),--verbose,)

.PHONY: help install install-skip-build clean clean-generated clean-build

help:
	@echo "Targets:"
	@echo "  make install AGENT=<agent> [SKILL_ROOT=<path>] [VERBOSE=1]  Run ./install.sh for an agent"
	@echo "  make install-skip-build AGENT=<agent> [VERBOSE=1]           Run installer without rebuilding a2a-send"
	@echo "  make clean                                      Remove generated install output and build artifacts"
	@echo "  make clean-generated                            Remove generated project-scoped skill/config dirs"
	@echo "  make clean-build                                Remove built a2a-send binary"
	@echo ""
	@echo "Supported AGENT values: claude-code, codex, opencode, copilot-cli"

install:
	./install.sh $(AGENT_ARG) $(INSTALL_FLAGS) $(VERBOSE_FLAG)

install-skip-build:
	./install.sh $(AGENT_ARG) $(INSTALL_FLAGS) --skip-build $(VERBOSE_FLAG)

clean: clean-generated clean-build

clean-generated:
	rm -rf .agntcy .claude .agents .opencode

clean-build:
	rm -f skills/a2a-messaging/scripts/a2a-send/a2a-send.bin
