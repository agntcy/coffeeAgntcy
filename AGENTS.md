# Agent context index

## Prompts

| Topic | File |
|-------|------|
| Release notes - version parameters | [.agents/prompts/release-notes/params.yaml](.agents/prompts/release-notes/params.yaml) |
| Release notes - generation spec | [.agents/prompts/release-notes/PROMPT.md](.agents/prompts/release-notes/PROMPT.md) |
| Release notes - style references | [.agents/prompts/release-notes/example.md](.agents/prompts/release-notes/example.md) |

## Skills

Grouped by concern - a new skill joins whichever group it fits, or starts a
new one (see `.agents/rules/formatting/organize-large-collections.md`).

### Domain (lungo)

| Topic | File |
|-------|------|
| Agentic Workflows API documentation (lungo) | [.agents/skills/domain-lungo/agentic-workflows-api-documentation-lungo/SKILL.md](.agents/skills/domain-lungo/agentic-workflows-api-documentation-lungo/SKILL.md) - `workflow-instance_api.md`; OpenAPI under `schema/openapi/` as HTTP contract (SSOT, not generated from code) |
| JSON Schema → Pydantic (lungo) | [.agents/skills/domain-lungo/jsonschema-to-pydantic-lungo/SKILL.md](.agents/skills/domain-lungo/jsonschema-to-pydantic-lungo/SKILL.md) |
| OpenAPI → Python (lungo) | [.agents/skills/domain-lungo/openapi-to-python-lungo/SKILL.md](.agents/skills/domain-lungo/openapi-to-python-lungo/SKILL.md) - routers/DTOs; OpenAPI unit tests |

### Repo tooling

| Topic | File |
|-------|------|
| Add a repository operation | [.agents/skills/repo-tooling/add-repo-operation/SKILL.md](.agents/skills/repo-tooling/add-repo-operation/SKILL.md) |
| Generate release notes | [.agents/skills/repo-tooling/generate-release-notes/SKILL.md](.agents/skills/repo-tooling/generate-release-notes/SKILL.md) |
| Manage repo tooling | [.agents/skills/repo-tooling/manage-repo-tooling/SKILL.md](.agents/skills/repo-tooling/manage-repo-tooling/SKILL.md) |
| Set up repo tooling | [.agents/skills/repo-tooling/setup-repo-tooling/SKILL.md](.agents/skills/repo-tooling/setup-repo-tooling/SKILL.md) |

### Quality checks

| Topic | File |
|-------|------|
| Auditing pipeline exceptions | [.agents/skills/quality-checks/auditing-pipeline-exceptions/SKILL.md](.agents/skills/quality-checks/auditing-pipeline-exceptions/SKILL.md) |
| Checking dashes | [.agents/skills/quality-checks/checking-dashes/SKILL.md](.agents/skills/quality-checks/checking-dashes/SKILL.md) |
| Checking Helm chart version bumps | [.agents/skills/quality-checks/checking-helm-chart-version-bumps/SKILL.md](.agents/skills/quality-checks/checking-helm-chart-version-bumps/SKILL.md) |
| Checking markdown links | [.agents/skills/quality-checks/checking-markdown-links/SKILL.md](.agents/skills/quality-checks/checking-markdown-links/SKILL.md) |
| Checking pinned references | [.agents/skills/quality-checks/checking-pinned-references/SKILL.md](.agents/skills/quality-checks/checking-pinned-references/SKILL.md) |
| Checking uv locks | [.agents/skills/quality-checks/checking-uv-locks/SKILL.md](.agents/skills/quality-checks/checking-uv-locks/SKILL.md) |
| Checking workflow permissions | [.agents/skills/quality-checks/checking-workflow-permissions/SKILL.md](.agents/skills/quality-checks/checking-workflow-permissions/SKILL.md) |
| Linting GitHub workflows | [.agents/skills/quality-checks/linting-github-workflows/SKILL.md](.agents/skills/quality-checks/linting-github-workflows/SKILL.md) |
| Linting shell scripts | [.agents/skills/quality-checks/linting-shell-scripts/SKILL.md](.agents/skills/quality-checks/linting-shell-scripts/SKILL.md) |
| Testing bash scripts | [.agents/skills/quality-checks/testing-bash-scripts/SKILL.md](.agents/skills/quality-checks/testing-bash-scripts/SKILL.md) |

### Process

| Topic | File |
|-------|------|
| Running a development iteration | [.agents/skills/process/running-a-development-iteration/SKILL.md](.agents/skills/process/running-a-development-iteration/SKILL.md) |

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

Grouped by concern, same reasoning as Skills above. `bash-script-testing`,
`helm-chart-version-bump`, `markdown-link-integrity`, `no-em-en-dashes`,
`pinned-external-references`, `shell-script-linting`, `uv-lock-sync`,
`workflow-file-linting`, and `workflow-least-privilege`are enforced
in CI; the rest rely on being applied by judgment.

### Meta (how this repo builds its own tooling)

| Topic | File |
|-------|------|
| Pinned tool versions | [.agents/rules/meta/pinned-tool-versions.md](.agents/rules/meta/pinned-tool-versions.md) |
| Repository operation pipeline | [.agents/rules/meta/repo-operation-pipeline.md](.agents/rules/meta/repo-operation-pipeline.md) |

### Process

| Topic | File |
|-------|------|
| Development iteration loop | [.agents/rules/process/development-iteration-loop.md](.agents/rules/process/development-iteration-loop.md) |
| Plan with OpenSpec | [.agents/rules/process/plan-with-openspec.md](.agents/rules/process/plan-with-openspec.md) |

### Always apply

| Topic | File |
|-------|------|
| Keep docs consistent | [.agents/rules/always-apply/keep-docs-consistent.md](.agents/rules/always-apply/keep-docs-consistent.md) |
| No em dashes or en dashes | [.agents/rules/always-apply/no-em-en-dashes.md](.agents/rules/always-apply/no-em-en-dashes.md) |
| Pre-finalize checks | [.agents/rules/always-apply/pre-finalize-checks.md](.agents/rules/always-apply/pre-finalize-checks.md) |
| Self-review after a change | [.agents/rules/always-apply/self-review-after-change.md](.agents/rules/always-apply/self-review-after-change.md) |

### Code/content quality

| Topic | File |
|-------|------|
| Bash script testing | [.agents/rules/quality/bash-script-testing.md](.agents/rules/quality/bash-script-testing.md) |
| Helm chart version bump | [.agents/rules/quality/helm-chart-version-bump.md](.agents/rules/quality/helm-chart-version-bump.md) |
| Markdown link integrity | [.agents/rules/quality/markdown-link-integrity.md](.agents/rules/quality/markdown-link-integrity.md) |
| Pinned external references | [.agents/rules/quality/pinned-external-references.md](.agents/rules/quality/pinned-external-references.md) |
| Shell script linting | [.agents/rules/quality/shell-script-linting.md](.agents/rules/quality/shell-script-linting.md) |
| uv lock sync | [.agents/rules/quality/uv-lock-sync.md](.agents/rules/quality/uv-lock-sync.md) |
| Workflow file linting | [.agents/rules/quality/workflow-file-linting.md](.agents/rules/quality/workflow-file-linting.md) |
| Workflow least privilege | [.agents/rules/quality/workflow-least-privilege.md](.agents/rules/quality/workflow-least-privilege.md) |

### Formatting & organization conventions

| Topic | File |
|-------|------|
| Alphabetize entity lists | [.agents/rules/formatting/alphabetize-entity-lists.md](.agents/rules/formatting/alphabetize-entity-lists.md) |
| File-tree comment alignment | [.agents/rules/formatting/file-tree-comment-alignment.md](.agents/rules/formatting/file-tree-comment-alignment.md) |
| Organize large collections | [.agents/rules/formatting/organize-large-collections.md](.agents/rules/formatting/organize-large-collections.md) |

## Repository references

| Topic | File |
|-------|------|
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| README (Built With format) | [README.md](README.md) |
