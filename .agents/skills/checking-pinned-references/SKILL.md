---
name: checking-pinned-references
description: >-
  Runs task pins:check to find any third-party GitHub Action,
  reusable-workflow, or image reference that isn't pinned to an immutable
  SHA/digest, and pins each one it finds. Use when adding or editing a
  `uses:` line, a Dockerfile FROM instruction, or a compose image: field.
---

# Checking pinned references

## What this skill does

Runs `task pins:check` (defined in [Taskfile.yaml](../../../Taskfile.yaml),
wrapping
[scripts/check_pinned_references.bash](../../../scripts/check_pinned_references.bash))
to scan every `.github/workflows/*.y*ml` `uses:` line, every Dockerfile
`FROM` instruction, and every compose `image:` field for a reference pinned
by a mutable tag/branch instead of an immutable commit SHA or image
digest. This is the same check `task check:all` runs as part of
[checks.yaml](../../../.github/workflows/checks.yaml). See
[.agents/rules/pinned-external-references.md](../../rules/pinned-external-references.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task pins:check
- [ ] 2. For each flagged GitHub Actions `uses:` line, find its commit SHA:
        gh api repos/<owner>/<repo>/commits/<tag> --jq '.sha' - then pin as
        owner/repo@<40-char-sha> # <tag>
- [ ] 3. For each flagged Docker image, find its digest:
        docker buildx imagetools inspect <image>:<tag> - then pin as
        image:<tag>@sha256:<digest>
- [ ] 4. If a reference genuinely can't be pinned (no tags/digests exist
        upstream), add a `# pin-exempt: <reason>` comment stating why,
        in place of the version comment
- [ ] 5. Re-run task pins:check to confirm it's clean
```

## Notes

- `pin-exempt` is a judgment call the person/agent adding the reference
  makes and justifies at the point it's added - don't reach for it just to
  silence the check.
- This only covers third-party references - an image this repo publishes
  itself (`ghcr.io/agntcy/coffee-agntcy/*`) using a floating tag like
  `:latest` in a dev compose file is normal usage, not a gap.
- If a new kind of floating reference shows up that
  `scripts/check_pinned_references.bash` doesn't scan for yet, extend the
  script to cover it rather than pinning by hand and leaving the gap for
  next time.
