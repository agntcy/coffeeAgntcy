# Agent context index

## Prompts

| Topic | File |
|-------|------|
| Release notes - version parameters | [.agents/prompts/release-notes/params.yaml](.agents/prompts/release-notes/params.yaml) |
| Release notes - generation spec | [.agents/prompts/release-notes/PROMPT.md](.agents/prompts/release-notes/PROMPT.md) |
| Release notes - style references | [.agents/prompts/release-notes/example.md](.agents/prompts/release-notes/example.md) |

## Skills

| Topic | File |
|-------|------|
| Generate release notes | [.agents/skills/generate-release-notes/SKILL.md](.agents/skills/generate-release-notes/SKILL.md) |
| OpenAPI → Python (lungo) | [.agents/skills/openapi-to-python-lungo/SKILL.md](.agents/skills/openapi-to-python-lungo/SKILL.md) - routers/DTOs; OpenAPI unit tests |
| JSON Schema → Pydantic (lungo) | [.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md](.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md) |
| Agentic Workflows API documentation (lungo) | [.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md](.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md) - `workflow-instance_api.md`; OpenAPI under `schema/openapi/` as HTTP contract (SSOT, not generated from code) |

## Rules

Conventions to apply proactively, not on request. None are enforced by
tooling yet - they rely on being applied by judgment.

| Topic | File |
|-------|------|
| Alphabetize entity lists | [.agents/rules/alphabetize-entity-lists.md](.agents/rules/alphabetize-entity-lists.md) |
| File-tree comment alignment | [.agents/rules/file-tree-comment-alignment.md](.agents/rules/file-tree-comment-alignment.md) |
| Keep docs consistent | [.agents/rules/keep-docs-consistent.md](.agents/rules/keep-docs-consistent.md) |
| No em dashes or en dashes | [.agents/rules/no-em-en-dashes.md](.agents/rules/no-em-en-dashes.md) |
| Organize large collections | [.agents/rules/organize-large-collections.md](.agents/rules/organize-large-collections.md) |
| Pinned external references | [.agents/rules/pinned-external-references.md](.agents/rules/pinned-external-references.md) |
| Self-review after a change | [.agents/rules/self-review-after-change.md](.agents/rules/self-review-after-change.md) |
| Workflow least privilege | [.agents/rules/workflow-least-privilege.md](.agents/rules/workflow-least-privilege.md) |

## Repository references

| Topic | File |
|-------|------|
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| README (Built With format) | [README.md](README.md) |
