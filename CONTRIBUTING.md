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
See [`.agents/rules/no-em-en-dashes.md`](/.agents/rules/no-em-en-dashes.md)
for the full rule. Run `task dashes:check` locally (`task dashes:fix` to
auto-fix); the `Checks` workflow (`checks.yaml`) fails the pull request if
either character appears. This is not covered by Ruff or EditorConfig.

#### Shell scripts

Every `.sh`/`.bash` file must pass shellcheck and shfmt (`-i 4 -ci`). See
[`.agents/rules/shell-script-linting.md`](/.agents/rules/shell-script-linting.md)
for the full rule. Run `task setup && source scripts/env.sh` once to
bootstrap a repo-local, pinned-version shellcheck/shfmt/actionlint into
`.tools/bin/` (no global install needed - see `scripts/setup.sh`), then
[`task`](https://taskfile.dev) `shell:lint` locally before opening a PR
(`task shell:fmt` to auto-fix formatting); the `Checks` workflow runs the
same check (along with every other standing check, via `task check:all`)
on every pull request.

#### Pinned external references and workflow permissions

Every third-party GitHub Action/reusable-workflow/image reference must be
pinned to an immutable SHA/digest (`task pins:check`), and every workflow
file must declare explicit, least-privilege permissions, never `write-all`
(`task workflows:check-permissions`). See
[`.agents/rules/pinned-external-references.md`](/.agents/rules/pinned-external-references.md)
and
[`.agents/rules/workflow-least-privilege.md`](/.agents/rules/workflow-least-privilege.md)
for the full rules. Both run as part of `task check:all` and the `Checks`
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
