# Agent context index

## Prompts

| Topic | File |
|-------|------|
| Release notes - version parameters | [.agents/prompts/release-notes/params.yaml](.agents/prompts/release-notes/params.yaml) |
| Release notes - generation spec | [.agents/prompts/release-notes/PROMPT.md](.agents/prompts/release-notes/PROMPT.md) |
| Release notes - style references | [.agents/prompts/release-notes/example.md](.agents/prompts/release-notes/example.md) |

## Skills

Grouped by concern - a new skill joins whichever group it fits, or starts a
new one (see `.agents/rules/organize-large-collections.md`).

### Domain (lungo)

| Topic | File |
|-------|------|
| Agentic Workflows API documentation (lungo) | [.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md](.agents/skills/agentic-workflows-api-documentation-lungo/SKILL.md) - `workflow-instance_api.md`; OpenAPI under `schema/openapi/` as HTTP contract (SSOT, not generated from code) |
| JSON Schema → Pydantic (lungo) | [.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md](.agents/skills/jsonschema-to-pydantic-lungo/SKILL.md) |
| OpenAPI → Python (lungo) | [.agents/skills/openapi-to-python-lungo/SKILL.md](.agents/skills/openapi-to-python-lungo/SKILL.md) - routers/DTOs; OpenAPI unit tests |

### Repo tooling

| Topic | File |
|-------|------|
| Add a repository operation | [.agents/skills/add-repo-operation/SKILL.md](.agents/skills/add-repo-operation/SKILL.md) |
| Generate release notes | [.agents/skills/generate-release-notes/SKILL.md](.agents/skills/generate-release-notes/SKILL.md) |
| Manage repo tooling | [.agents/skills/manage-repo-tooling/SKILL.md](.agents/skills/manage-repo-tooling/SKILL.md) |
| Set up repo tooling | [.agents/skills/setup-repo-tooling/SKILL.md](.agents/skills/setup-repo-tooling/SKILL.md) |

### Quality checks

| Topic | File |
|-------|------|
| Checking dashes | [.agents/skills/checking-dashes/SKILL.md](.agents/skills/checking-dashes/SKILL.md) |
| Checking pinned references | [.agents/skills/checking-pinned-references/SKILL.md](.agents/skills/checking-pinned-references/SKILL.md) |
| Checking workflow permissions | [.agents/skills/checking-workflow-permissions/SKILL.md](.agents/skills/checking-workflow-permissions/SKILL.md) |
| Linting GitHub workflows | [.agents/skills/linting-github-workflows/SKILL.md](.agents/skills/linting-github-workflows/SKILL.md) |
| Linting shell scripts | [.agents/skills/linting-shell-scripts/SKILL.md](.agents/skills/linting-shell-scripts/SKILL.md) |

### OpenSpec workflow

Generated and kept in sync by the `openspec` CLI itself (`openspec update`
regenerates these) - not hand-authored like the skills above. See the
`plan-with-openspec` rule for when this workflow applies.

| Topic | File |
|-------|------|
| openspec-apply-change | [.agents/skills/openspec-apply-change/SKILL.md](.agents/skills/openspec-apply-change/SKILL.md) - implementing, or continuing to implement, a change's tasks |
| openspec-archive-change | [.agents/skills/openspec-archive-change/SKILL.md](.agents/skills/openspec-archive-change/SKILL.md) - finalizing a completed change into `openspec/specs/` |
| openspec-explore | [.agents/skills/openspec-explore/SKILL.md](.agents/skills/openspec-explore/SKILL.md) - thinking through an idea before or during a change |
| openspec-propose | [.agents/skills/openspec-propose/SKILL.md](.agents/skills/openspec-propose/SKILL.md) - proposing a change with proposal/design/spec delta/tasks in one step |
| openspec-sync-specs | [.agents/skills/openspec-sync-specs/SKILL.md](.agents/skills/openspec-sync-specs/SKILL.md) - syncing a change's delta spec into main specs without archiving |
| openspec-update-change | [.agents/skills/openspec-update-change/SKILL.md](.agents/skills/openspec-update-change/SKILL.md) - revising an already-proposed change's artifacts |

## Rules

Grouped by concern, same reasoning as Skills above. `no-em-en-dashes`,
`pinned-external-references`, `shell-script-linting`,
`workflow-file-linting`, and `workflow-least-privilege` are enforced in
CI; the rest rely on being applied by judgment.

### Meta (how this repo builds its own tooling)

| Topic | File |
|-------|------|
| Pinned tool versions | [.agents/rules/pinned-tool-versions.md](.agents/rules/pinned-tool-versions.md) |
| Repository operation pipeline | [.agents/rules/repo-operation-pipeline.md](.agents/rules/repo-operation-pipeline.md) |

### Process

| Topic | File |
|-------|------|
| Plan with OpenSpec | [.agents/rules/plan-with-openspec.md](.agents/rules/plan-with-openspec.md) |

### Always apply

| Topic | File |
|-------|------|
| Keep docs consistent | [.agents/rules/keep-docs-consistent.md](.agents/rules/keep-docs-consistent.md) |
| No em dashes or en dashes | [.agents/rules/no-em-en-dashes.md](.agents/rules/no-em-en-dashes.md) |
| Pre-finalize checks | [.agents/rules/pre-finalize-checks.md](.agents/rules/pre-finalize-checks.md) |
| Self-review after a change | [.agents/rules/self-review-after-change.md](.agents/rules/self-review-after-change.md) |

### Code/content quality

| Topic | File |
|-------|------|
| Pinned external references | [.agents/rules/pinned-external-references.md](.agents/rules/pinned-external-references.md) |
| Shell script linting | [.agents/rules/shell-script-linting.md](.agents/rules/shell-script-linting.md) |
| Workflow file linting | [.agents/rules/workflow-file-linting.md](.agents/rules/workflow-file-linting.md) |
| Workflow least privilege | [.agents/rules/workflow-least-privilege.md](.agents/rules/workflow-least-privilege.md) |

### Formatting & organization conventions

| Topic | File |
|-------|------|
| Alphabetize entity lists | [.agents/rules/alphabetize-entity-lists.md](.agents/rules/alphabetize-entity-lists.md) |
| File-tree comment alignment | [.agents/rules/file-tree-comment-alignment.md](.agents/rules/file-tree-comment-alignment.md) |
| Organize large collections | [.agents/rules/organize-large-collections.md](.agents/rules/organize-large-collections.md) |

## Repository references

| Topic | File |
|-------|------|
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| README (Built With format) | [README.md](README.md) |
