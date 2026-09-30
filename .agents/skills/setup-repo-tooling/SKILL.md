---
name: setup-repo-tooling
description: >-
  Bootstraps this repo's toolchain (task, actionlint, shellcheck, shfmt,
  node, openspec) into repo-local .tools/bin and .tools/node/bin
  directories and puts both on PATH for the session. Use before running any
  other task in this repo, or whenever `task`, `actionlint`, `shellcheck`,
  `shfmt`, `node`, `npm`, or `openspec` are reported as not found.
---

# Set up repo tooling

## When to use

Before doing anything else in this repo, or when a command fails with
`task: command not found` / `actionlint: command not found` / `shellcheck:
command not found` / `shfmt: command not found` / `node: command not
found` / `npm: command not found` / `openspec: command not found`.

This skill is the one deliberate exception to the script -> Taskfile task
-> skill hierarchy described in
[`.agents/rules/repo-operation-pipeline.md`](../../rules/repo-operation-pipeline.md):
it calls `scripts/setup.sh` directly rather than through a `task` command,
because `task` itself doesn't exist yet on a fresh clone - bootstrapping it
*through* the Taskfile would be circular.

## What it does

`scripts/setup.sh` installs `task`, `actionlint`, `shellcheck`, `shfmt`,
`node`, and `openspec` into `.tools/` - inside this repo only, never the
user's global PATH, shell profile, or home directory - and is safe to
re-run any time (it's a no-op if everything is already present at its
pinned version, per
[`.agents/rules/pinned-tool-versions.md`](../../rules/pinned-tool-versions.md)).
If neither `curl` nor `wget` is present, it installs `curl` itself via
whatever OS package manager is already on the machine (or prints manual
instructions if it can't).

`openspec` (`@fission-ai/openspec`) ships as an npm package rather than a
standalone binary, so `setup.sh` bootstraps its own pinned Node.js first
and installs `openspec` with that Node's `npm`. Node lands in
`.tools/node/` rather than the flat `.tools/bin/`, because its `npm`/`npx`
are symlinks resolved relative to a sibling `lib/node_modules/npm/` and
can't be moved independently of that directory the way every other tool's
single relocatable binary can - `scripts/env.sh` puts both `.tools/bin`
and `.tools/node/bin` on PATH to cover it.

## Steps

```
- [ ] 1. Run: ./scripts/setup.sh
- [ ] 2. Run: source scripts/env.sh   (puts .tools/bin and .tools/node/bin on PATH for this shell)
- [ ] 3. Confirm: task --list         (should print every task with no errors)
```

If `task` is already on `PATH` some other way (e.g. installed via a
package manager), `task setup` does the same thing as step 1 - either
entry point runs the identical idempotent script.

## Rules

- Never hand-install `task`/`actionlint`/`shellcheck`/`shfmt`/`node` some
  other way (Homebrew, apt, nvm, a differently pinned curl command) -
  always go through `scripts/setup.sh` so the version pinned in
  [`scripts/lib/versions.sh`](../../../scripts/lib/versions.sh) is what
  actually gets used.
- If a pinned version needs bumping, or a tool needs to be added to or
  removed from the toolchain, see the `manage-repo-tooling` skill - do not
  hardcode a version anywhere else.
