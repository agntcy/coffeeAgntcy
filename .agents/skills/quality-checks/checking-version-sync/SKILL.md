---
name: checking-version-sync
description: >-
  Runs task versions:check to confirm every Node install reads NODE_VERSION
  from scripts/lib/versions.sh, and that the UI image digest, frontend
  engines.node floors, and the docs that state the Node version match it.
  Use when changing a Node install, NODE_VERSION, docker/Dockerfile.ui, a
  frontend engines field, or those docs.
---

# Checking Node version sync

## What this skill does

Runs `task versions:check` (defined in
[Taskfile.yaml](../../../../Taskfile.yaml), wrapping
[scripts/checks/check_versions.bash](../../../../scripts/checks/check_versions.bash))
to confirm Node installs read `NODE_VERSION` from
[scripts/lib/versions.sh](../../../../scripts/lib/versions.sh), and that
the UI image digest, the frontend `engines.node` floors, and the docs
that state the Node version match it. This is the same check
`task check:all` runs as part of
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/version-sync.md](../../../rules/quality/version-sync.md)
for the underlying rule.

The script checks Node only. Other pins in `versions.sh` are out of scope.

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
- [ ] 4. Re-run task versions:check to confirm it's clean
```

## Notes

- `source scripts/env.sh` exports `NODE_VERSION` for local UI builds. It
  does not export the other pins.
- `task tools:sync-node` does not talk to the registry when
  `scripts/lib/node-image.txt` already records the current `NODE_VERSION`
  and the consumers already agree.
