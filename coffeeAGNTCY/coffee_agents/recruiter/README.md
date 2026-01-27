# Agent Recruiter

Generalized agent discovery, evaluation, and task-based agent recruiting.

<img alt="" src="design-docs/recruiter-architecture.png">

1. Requester asks Recruiter to find an agent that meets the enterprise requirements and evaluation criteria.
2. Recruiter searches configured agent registries for agents that meet criteria
3. Recruiter screens and evaluates agent candidates by creating A2A or MCP clients and starting interviewer round
4. A list of interviewed agents, the transcript and score are returned

## Getting Started

**Example Agents**
```
uv run python test/example-agents/upload_cards.py
```

```
uv pip install ".[dev]"
```

```
uv run python test/example-agents/hello_world/__main__.py
```

### Dev runs
```
adk web src
```
