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
| Add a repository operation | [.agents/skills/add-repo-operation/SKILL.md](.agents/skills/add-repo-operation/SKILL.md) |
| Agentic Workflows API documentation (lungo) | [.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md](.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md) - `workflow-instance_api.md`; OpenAPI under `schema/openapi/` as HTTP contract (SSOT, not generated from code) |
| Checking dashes | [.agents/skills/checking-dashes/SKILL.md](.agents/skills/checking-dashes/SKILL.md) |
| Checking pinned references | [.agents/skills/checking-pinned-references/SKILL.md](.agents/skills/checking-pinned-references/SKILL.md) |
| Checking workflow permissions | [.agents/skills/checking-workflow-permissions/SKILL.md](.agents/skills/checking-workflow-permissions/SKILL.md) |
| Generate release notes | [.agents/skills/generate-release-notes/SKILL.md](.agents/skills/generate-release-notes/SKILL.md) |
| JSON Schema → Pydantic (lungo) | [.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md](.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md) |
| Linting GitHub workflows | [.agents/skills/linting-github-workflows/SKILL.md](.agents/skills/linting-github-workflows/SKILL.md) |
| Linting shell scripts | [.agents/skills/linting-shell-scripts/SKILL.md](.agents/skills/linting-shell-scripts/SKILL.md) |
| Manage repo tooling | [.agents/skills/manage-repo-tooling/SKILL.md](.agents/skills/manage-repo-tooling/SKILL.md) |
| OpenAPI → Python (lungo) | [.agents/skills/openapi-to-python-lungo/SKILL.md](.agents/skills/openapi-to-python-lungo/SKILL.md) - routers/DTOs; OpenAPI unit tests |
| Set up repo tooling | [.agents/skills/setup-repo-tooling/SKILL.md](.agents/skills/setup-repo-tooling/SKILL.md) |

## Rules

Conventions to apply proactively, not on request. `no-em-en-dashes`,
`pinned-external-references`, `shell-script-linting`,
`workflow-file-linting`, and `workflow-least-privilege` are enforced in
CI; the rest rely on being applied by judgment.

| Topic | File |
|-------|------|
| Alphabetize entity lists | [.agents/rules/alphabetize-entity-lists.md](.agents/rules/alphabetize-entity-lists.md) |
| File-tree comment alignment | [.agents/rules/file-tree-comment-alignment.md](.agents/rules/file-tree-comment-alignment.md) |
| Keep docs consistent | [.agents/rules/keep-docs-consistent.md](.agents/rules/keep-docs-consistent.md) |
| No em dashes or en dashes | [.agents/rules/no-em-en-dashes.md](.agents/rules/no-em-en-dashes.md) |
| Organize large collections | [.agents/rules/organize-large-collections.md](.agents/rules/organize-large-collections.md) |
| Pinned external references | [.agents/rules/pinned-external-references.md](.agents/rules/pinned-external-references.md) |
| Pinned tool versions | [.agents/rules/pinned-tool-versions.md](.agents/rules/pinned-tool-versions.md) |
| Pre-finalize checks | [.agents/rules/pre-finalize-checks.md](.agents/rules/pre-finalize-checks.md) |
| Repository operation pipeline | [.agents/rules/repo-operation-pipeline.md](.agents/rules/repo-operation-pipeline.md) |
| Self-review after a change | [.agents/rules/self-review-after-change.md](.agents/rules/self-review-after-change.md) |
| Shell script linting | [.agents/rules/shell-script-linting.md](.agents/rules/shell-script-linting.md) |
| Workflow file linting | [.agents/rules/workflow-file-linting.md](.agents/rules/workflow-file-linting.md) |
| Workflow least privilege | [.agents/rules/workflow-least-privilege.md](.agents/rules/workflow-least-privilege.md) |

## Repository references

| Topic | File |
|-------|------|
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| README (Built With format) | [README.md](README.md) |
