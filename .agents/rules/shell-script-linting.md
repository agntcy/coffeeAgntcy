---
name: shell-script-linting
description: >-
  Every shell script in this repo (`.sh`/`.bash`) must pass shellcheck
  (static analysis) and shfmt (formatting, `-i 4 -ci`) before being
  considered finished. Apply whenever writing or editing a shell script.
  Checked by `task shell:lint` (scripts/lint_shell.bash), which also runs
  as part of `task check:all` in .github/workflows/checks.yaml.
---

# Shell script linting

## Rule

Every shell script in this repo - anywhere, not only under `scripts/` -
must pass both:

- **shellcheck** (<https://github.com/koalaman/shellcheck>): static
  analysis for common shell bugs (unquoted expansions, unreachable code,
  wrong test operators, and similar).
- **shfmt** (<https://github.com/mvdan/sh>): formatting, pinned to `-i 4
  -ci` (4-space indent, switch-case bodies indented) to match the style
  already used by
  `coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh`.

Run `task shell:lint` before treating any shell script change as finished,
and fix everything it reports - don't leave a script that fails either tool
for CI to catch later.

## Why

Shell's quoting and word-splitting rules make it easy to write a script
that looks correct and works on the author's machine but breaks on an
unquoted variable containing a space, a glob, or an unexpected empty
value - shellcheck catches this class of bug at review time instead of in
production. Formatting drift (tabs vs. spaces, inconsistent indent width)
compounds across scripts written by different contributors and agents;
shfmt removes the drift the same way `ruff format`/`prettier` do for the
other languages in this repo.

## How to apply

- After writing or editing any `.sh`/`.bash` file, run `task shell:lint`
  (wraps `scripts/lint_shell.bash`, see
  [Taskfile.yaml](../../Taskfile.yaml)) and fix every shellcheck finding and
  shfmt diff it reports.
- `task shell:fmt` rewrites files in place with shfmt; still run `task
  shell:lint` afterward, since shfmt doesn't fix shellcheck findings.
- Install locally: `task setup` (or `./scripts/setup.sh`) bootstraps
  shellcheck and shfmt, pinned to the versions in
  [scripts/lib/versions.sh](../../scripts/lib/versions.sh), into
  `.tools/bin/` - no global install needed. Run `source scripts/env.sh` to
  put them on `PATH`. `task shell:lint`/`shell:fmt` fall back to a
  PATH-installed shellcheck/shfmt if `.tools/bin/` is empty.
- CI enforces this on every push/PR: `task check:all` in
  [.github/workflows/checks.yaml](../../.github/workflows/checks.yaml)
  runs `shell:lint` alongside every other standing check - a red job means
  some script in the diff needs fixing before merging.
- See the `linting-shell-scripts` skill for the full workflow.
