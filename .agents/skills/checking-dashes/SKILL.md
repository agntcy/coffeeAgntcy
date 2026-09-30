---
name: checking-dashes
description: >-
  Runs task dashes:check against the whole repo for an em dash or en dash
  and fixes any hit with task dashes:fix. Use before finishing any change
  that includes prose or comments, or when asked to check for or remove
  em/en dashes.
---

# Checking dashes

## What this skill does

Runs `task dashes:check` (defined in [Taskfile.yaml](../../../Taskfile.yaml),
wrapping [scripts/check_dashes.bash](../../../scripts/check_dashes.bash)) to
scan the whole repo for an em dash (U+2014) or en dash (U+2013), then fixes
any hit with `task dashes:fix`. This is the same check `task check:all`
runs as part of [checks.yaml](../../../.github/workflows/checks.yaml). See
[.agents/rules/no-em-en-dashes.md](../../rules/no-em-en-dashes.md) for the
underlying rule.

## Workflow

```
- [ ] 1. Run: task dashes:check
- [ ] 2. If it reports hits, run: task dashes:fix (replaces every hit with
        a plain ASCII hyphen in place)
- [ ] 3. Re-run task dashes:check to confirm it's clean
```

## Notes

- `task dashes:fix` only replaces the character - re-read the surrounding
  text afterward, since a bare substitution can occasionally leave odd
  spacing when the character had no spaces around it to begin with.
- Never write the literal em dash or en dash character in a rule/skill
  file that documents this check - name it by Unicode code point instead
  (see how `.agents/rules/no-em-en-dashes.md` itself does this), or the
  file will trip the very check it describes.
