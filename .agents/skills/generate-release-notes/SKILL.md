---
name: generate-release-notes
description: >-
  Generates coffeeAgntcy CHANGELOG release notes and README Built With updates from
  PRs and dependency lockfiles since the previous release tag. Use when the user asks
  for release notes, a changelog entry, GitHub release text, or preparing a semver release.
disable-model-invocation: true
---

# Generate release notes (coffeeAgntcy)

## Inputs

| File | Purpose |
|------|---------|
| [.agents/prompts/release-notes/params.yaml](../../prompts/release-notes/params.yaml) | `previous_version`, `current_version`, repo identifiers |
| [.agents/prompts/release-notes/PROMPT.md](../../prompts/release-notes/PROMPT.md) | Full generation spec |
| [.agents/prompts/release-notes/example.md](../../prompts/release-notes/example.md) | Pointers to gold-standard examples |

## Workflow

```
- [ ] 1. Read params.yaml — confirm versions with the user if missing or stale
- [ ] 2. Read PROMPT.md — follow it verbatim for structure and output rules
- [ ] 3. Read CHANGELOG.md — previous release section + example section from example.md
- [ ] 4. Collect changes since previous_version (PRs on default branch; direct commits only when no PR)
- [ ] 5. Read dependency lockfiles listed in PROMPT.md
- [ ] 6. Read README.md Built With section for formatting reference
- [ ] 7. Output two markdown code blocks — do not edit files unless asked
```

## Discovery commands

Use when the user has not supplied a PR list:

```bash
git tag -l 'v*' --sort=-version:refname | head
git log v{previous_version}..HEAD --merges --oneline
gh pr list --repo {github_repo} --state merged --base main --limit 100
```

Substitute `{previous_version}`, `{current_version}`, and `{github_repo}` from `params.yaml`. Prefix tags with `v` only if that matches existing tags in the repo.

## Rules

- Follow [PROMPT.md](../../prompts/release-notes/PROMPT.md) for structure, contributor omit list, and HTML `<details>` format.
- Do not paraphrase or shorten the user's spec; apply it as written.
- Default: generate text only. Edit `CHANGELOG.md` or `README.md` only when the user explicitly requests file changes.