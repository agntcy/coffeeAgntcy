.PHONY: test-agent build-a2a-send

test-agent:
	uv venv
	uv sync
	. .venv/bin/activate && adk web

build-a2a-send:
	cd coding-agent-integrations/claude-code/plugin/scripts/a2a-send && go build -o a2a-send .
