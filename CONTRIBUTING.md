# How to Contribute

Thanks for your interest in contributing to `coffeeAgntcy`! Here are a few
general guidelines on contributing and reporting bugs that we ask you to review.
Following these guidelines helps to communicate that you respect the time of the
contributors managing and developing this open source project. In return, they
should reciprocate that respect in addressing your issue, assessing changes, and
helping you finalize your pull requests. In that spirit of mutual respect, we
endeavor to review incoming issues and pull requests within 10 days, and will
close any lingering issues or pull requests after 60 days of inactivity.

Please note that all of your interactions in the project are subject to our
[Code of Conduct](/CODE_OF_CONDUCT.md). This includes creation of issues or pull
requests, commenting on issues or pull requests, and extends to all interactions
in any real-time space e.g., Slack, Discord, etc.

## Reporting Issues

Before reporting a new issue, please ensure that the issue was not already
reported or fixed by searching through our [issues
list](https://github.com/agntcy/coffeeAgntcy/issues).

When creating a new issue, please be sure to include a **title and clear
description**, as much relevant information as possible, and, if possible, a
test case.

**If you discover a security bug, please do not report it through GitHub.
Instead, please see security procedures in [SECURITY.md](/SECURITY.md).**

## Sending Pull Requests

Before sending a new pull request, take a look at existing pull requests and
issues to see if the proposed change or fix has been discussed in the past, or
if the change was already implemented but not yet released.

We expect new pull requests to include tests for any affected behavior, and, as
we follow semantic versioning, we may reserve breaking changes until the next
major version release.

Each agent project documents its test layout and commands in `tests/README.md` under `coffeeAGNTCY/coffee_agents/{corto,lungo,recruiter}/`.

If your PR changes a Helm chart's contents (anything under a chart's `deployment/helm/<chart>/` directory), bump that chart's `version:` field in its `Chart.yaml`. Helm charts aren't tagged in git - the `Chart.yaml` version is the only thing that identifies a published chart, so an unbumped version on changed content will be rejected: `helm-push.yaml`'s CI guard fails the workflow if a chart is pushed under a version that already exists in GHCR. See [`docs/RELEASE-OPS.md`](docs/RELEASE-OPS.md) for how this is audited before each release.

## Planning a feature or substantial change

A routine, self-contained change (a bug fix, a small doc update, a single
new script that doesn't ripple elsewhere) keeps the normal PR flow above.
For anything bigger (a new tool/script/CI check, a schema or repo-wide
convention change, or anything else that spans more than a small diff),
plan it with [OpenSpec](https://openspec.dev) before writing any code:

1. **Set up tooling once**, if you haven't: `./scripts/setup.sh && source
   scripts/env.sh` installs `openspec` alongside the rest of this repo's
   local toolchain (see
   [`.agents/skills/repo-tooling/setup-repo-tooling/SKILL.md`](.agents/skills/repo-tooling/setup-repo-tooling/SKILL.md)).
   `task` isn't on `PATH` until this has run at least once on a fresh
   clone, so this is the one place this repo asks for the plain script
   instead of a `task` command - `task setup` works too, but only once
   `task` is already available some other way.
2. **Propose it:** `openspec propose` - describe what you want to build;
   it generates a proposal, design, spec delta, and tasks list under
   `openspec/changes/<name>/`. Get that plan right before implementing -
   this is the point to catch a bad approach cheaply, not after the diff
   exists.
3. **Implement it:** `openspec apply`, or work through `tasks.md` by hand,
   then follow the rest of this repo's normal flow (`task check:all`, the
   linting sections below) before opening the PR.
4. **Archive it** once the PR merges: `openspec archive` moves the
   change's rationale and final spec delta into `openspec/specs/`, so it
   stays discoverable after the PR itself is buried in history.

This is an added planning step before code, not a different approval
process - everything above still applies once the PR is open. If you're an
agent, the generated `.agents/skills/openspec-*` skills (indexed in
[AGENTS.md](AGENTS.md)) are the entry point, not these CLI commands
directly. See [`.agents/rules/process/plan-with-openspec.md`](.agents/rules/process/plan-with-openspec.md)
for the full rule.

### Linting and code style

This section is the home for the lint and style rules that apply to
`coffeeAgntcy`. Each rule below states what the code must look like, which CI
workflow enforces it, and how to run the same check locally before opening a
pull request. Further rules will be added here as they are adopted.

#### Python indentation

Python sources use **4 spaces per indent level, never tabs** (PEP 8). Both
halves of that rule are enforced: `W191` and `E101` reject tabs and mixed
tabs/spaces, and `E111`, `E114`, and `E117` reject any indent that is not a
multiple of four. A file indented consistently with 2 spaces fails.

The `Python lint` workflow runs `ruff check` for `corto`, `lungo`, and
`recruiter` on every pull request; it lints only and never reformats. Locally,
after `uv sync --extra dev` in a backend package, run `uv run ruff check .`.
To apply the formatter, run `uv run ruff format .` -- Ruff-aware editors pick
the same settings up from `[tool.ruff.format]` in that package's
`pyproject.toml`. Editors that honor EditorConfig apply 4-space Python indent
from the repo-root `.editorconfig` on new edits.

#### ASCII hyphens only

Do not use en dash (U+2013) or em dash (U+2014) anywhere in the repository
(including comments, markdown, and EditorConfig). Use ASCII `-` or `--`.
See [`.agents/rules/always-apply/no-em-en-dashes.md`](/.agents/rules/always-apply/no-em-en-dashes.md)
for the full rule. Run `task dashes:check` locally (`task dashes:fix` to
auto-fix); the `Checks` workflow (`checks.yaml`) fails the pull request if
either character appears. This is not covered by Ruff or EditorConfig.

#### Shell scripts

Every `.sh`/`.bash` file must pass shellcheck and shfmt (`-i 4 -ci`). See
[`.agents/rules/quality/shell-script-linting.md`](/.agents/rules/quality/shell-script-linting.md)
for the full rule. Run `./scripts/setup.sh && source scripts/env.sh` once
to bootstrap a repo-local, pinned-version shellcheck/shfmt/actionlint into
`.tools/bin/` (no global install needed - `task` itself isn't on `PATH`
until this has run, so use the plain script rather than `task setup` on a
fresh clone; see `scripts/setup.sh`), then [`task`](https://taskfile.dev)
`shell:lint` locally before opening a PR (`task shell:fmt` to auto-fix
formatting); the `Checks` workflow runs the same check (along with every
other standing check, via `task check:all`) on every pull request.

`scripts/lint/lint_shell.bash` (like `scripts/checks/find_strings.bash` and
`scripts/checks/check_pinned_references.bash`) uses Bash 4 features
(`mapfile`, associative arrays). Stock macOS ships Bash 3.2; macOS
contributors need a newer Bash on `PATH` (e.g. `brew install bash`) to run
these scripts directly.

#### Bash script tests

A new bash script anywhere in the repository needs tests: a shared `*/lib/*.sh`-style
helper gets unit tests (`task tests:bash`), and an executable script gets
a mocked end-to-end test with any external command it depends on stubbed.
See [`.agents/rules/quality/bash-script-testing.md`](/.agents/rules/quality/bash-script-testing.md)
for the full rule - it doesn't require retrofitting tests onto a script
that already existed before this rule. `task tests:coverage` flags a
script with neither a test nor an explicit grandfather-list entry. Both
run as part of `task check:all` and the `Checks` workflow.

#### Pinned external references and workflow permissions

Every third-party GitHub Action/reusable-workflow/image reference must be
pinned to an immutable SHA/digest (`task pins:check`), and every workflow
file must declare explicit, least-privilege permissions, never `write-all`
(`task workflows:check-permissions`). See
[`.agents/rules/quality/pinned-external-references.md`](/.agents/rules/quality/pinned-external-references.md)
and
[`.agents/rules/quality/workflow-least-privilege.md`](/.agents/rules/quality/workflow-least-privilege.md)
for the full rules. Both run as part of `task check:all` and the `Checks`
workflow.

#### Markdown links

Every relative link in a markdown file must resolve to a file that
actually exists (`task links:check`) - check this after moving, renaming,
or removing any file. See
[`.agents/rules/quality/markdown-link-integrity.md`](/.agents/rules/quality/markdown-link-integrity.md)
for the full rule. Runs as part of `task check:all` and the `Checks`
workflow.

## Other Ways to Contribute

We welcome anyone that wants to contribute to `coffeeAgntcy` to triage and
reply to open issues to help troubleshoot and fix existing bugs. Here is what
you can do:

- Help ensure that existing issues follows the recommendations from the
  _[Reporting Issues](#reporting-issues)_ section, providing feedback to the
  issue's author on what might be missing.
- Review existing pull requests, and testing patches against real existing
  applications that use `coffeeAgntcy`.
- Write a test, or add a missing test case to an existing test.

Thanks again for your interest on contributing to `coffeeAgntcy`!

:heart:
