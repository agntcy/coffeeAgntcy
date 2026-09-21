---
name: pinned-external-references
description: >-
  Any reference this repo makes to third-party code or images by a mutable
  identifier (a Git tag/branch, a Docker image tag, a package's "latest") -
  wherever it appears - should be pinned to an immutable identifier (a full
  commit SHA, an image digest) instead, with the version it corresponds to
  kept nearby. Apply whenever adding or editing such a reference. State a
  `# pin-exempt: <reason>` comment for any case that genuinely can't be
  pinned.
---

# Pinned external references

## Rule

Any reference this repo makes to third-party code or images by a mutable,
retargetable identifier should instead be pinned to an immutable one, with
the human-readable version it corresponds to kept nearby - wherever that
reference appears, not only in `.github/workflows/`. Concretely, today:

```yaml
# GitHub Actions/reusable workflows: pin to the commit SHA, comment the tag
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
```

```dockerfile
# Docker images: pin to the digest; keep the tag alongside it when there is one
FROM golang:1.22.5@sha256:2c5995...c0a1 AS builder
```

```yaml
# docker-compose/compose: same as Dockerfiles
image: nginx:1.27.3@sha256:9f8b2b...e14f
```

The same principle applies to any other floating reference this repo comes
to depend on - a Helm chart version, a Go/Python dependency pulled straight
from a Git ref instead of a registry, a `curl | sh` install pinned only to
"latest", and so on - pin whichever of those the ecosystem supports pinning
by immutable identifier, wherever it shows up.

If a given reference genuinely can't be pinned this way (no tags/digests
exist upstream to pin to, the ecosystem has no immutable identifier at
all, ...), the developer adding it states that explicitly with a
`# pin-exempt: <reason>` comment in place of the version comment, rather
than leaving it floating silently:

```yaml
- uses: some-org/some-action@main # pin-exempt: no tagged releases published upstream, reviewed each bump
```

`pin-exempt` is a judgment call for a human to make and justify at the
point the reference is added - not something to reach for by default.

## Why

A tag, branch, or "latest" is a floating pointer - whoever controls the
upstream repo or registry (or an attacker who compromises their account)
can retarget it to different code at any time, and everything referencing
it silently starts running whatever it now points to on its next run, with
no diff to review. An immutable identifier (a commit SHA, an image digest)
turns that into an explicit, reviewable change instead of a silent one. The
version kept alongside it exists because a bare SHA or digest is
meaningless to a human skimming the file - it records which release the pin
was made against, so a future bump is a matter of diffing tags rather than
archaeology.

## How to apply

- To find the commit SHA for a tag: `gh api
  repos/<owner>/<repo>/commits/<tag> --jq '.sha'`. (Don't use
  `git/refs/tags/<tag>` - for an annotated tag `.object.sha` is the tag
  object's SHA, not the commit's.) To find an image digest for a tag:
  `docker buildx imagetools inspect <image>:<tag>`.
- There is no automated check for this yet, so apply it by judgment on every
  new or edited reference.
- Use `# pin-exempt: <reason>` sparingly and only with a real reason - it's
  a stated exception for when pinning isn't possible, not a shortcut for
  skipping the lookup.
