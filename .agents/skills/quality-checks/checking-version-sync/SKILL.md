---
name: checking-version-sync
description: >-
  Runs task versions:check to confirm every versions.sh pin is the only
  copy of that tool. Use when changing a pin, a Node or uv install,
  docker/Dockerfile.ui, docker/Dockerfile.python-agent, a frontend
  engines field, or a doc that states the Node version.
---

# Checking version sync

## What this skill does

Runs `task versions:check` (defined in
[Taskfile.yaml](../../../../Taskfile.yaml), wrapping
[scripts/checks/check_versions.bash](../../../../scripts/checks/check_versions.bash))
to confirm every pin in
[scripts/lib/versions.sh](../../../../scripts/lib/versions.sh) is the only
copy of that tool. This is the same check `task check:all` runs as part
of [checks.yaml](../../../../.github/workflows/checks.yaml). The map of
every pin is [docs/tool-versions.md](../../../../docs/tool-versions.md),
and the Node procedure is
[docs/node-version.md](../../../../docs/node-version.md). See
[.agents/rules/quality/version-sync.md](../../../rules/quality/version-sync.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task versions:check
- [ ] 2. For a hardcoded node-version, FROM node tag, or compose
        NODE_VERSION value, delete the literal and read NODE_VERSION
        (source scripts/lib/versions.sh, or pass the build-arg)
- [ ] 3. For a digest, engines.node floor, or doc sentence that disagrees
        with NODE_VERSION, run: task tools:sync-node
        Review the new digest against
        docker buildx imagetools inspect node:<NODE_VERSION>-alpine
- [ ] 4. For a numeric uv tag, a Helm version literal, a lockfile
        openspec or renovate version, or an OpenSpec generatedBy stamp
        that disagrees, read the pin. For a stale generatedBy stamp,
        run: task tools:sync-openspec. For a tool install the check
        reports "outside scripts/setup.sh" or an action that installs
        actionlint, bats, shellcheck, shfmt, or task, replace the action
        or install line with a task command (scripts/setup.sh installs
        the tool at its pin). For a test-reusable.yaml message that it
        does not source versions.sh or export NODE_VERSION or
        UV_VERSION, restore the "Export image build pins" step in
        .github/workflows/test-reusable.yaml (a comment copy of it does
        not count). For a setup-uv step that reports
        "without passing UV_VERSION", export UV_VERSION from
        scripts/lib/versions.sh into $GITHUB_ENV and pass
        version: ${{ env.UV_VERSION }}. For the uv digest, run:
        task tools:sync-uv
- [ ] 5. Re-run task versions:check to confirm it's clean
```

## Notes

- `source scripts/env.sh` exports `NODE_VERSION` and `UV_VERSION` for
  local image builds. It does not export the other pins.
- `.github/workflows/test-reusable.yaml` sources `scripts/lib/versions.sh`
  and exports those two pins before pytest. `task versions:check` fails
  when that export is missing or is a literal.
- `task tools:sync-node` does not talk to the registry when
  `scripts/lib/node-image.txt` already records the current `NODE_VERSION`
  and the consumers already agree.
