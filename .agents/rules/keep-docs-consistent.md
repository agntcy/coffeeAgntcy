---
name: keep-docs-consistent
description: >-
  After any change - not only a change to a doc file itself - check every
  documentation surface in the repo for anything that now describes the old
  state, and update it in the same change. Apply as part of the final
  review of any non-trivial change.
---

# Keep documentation consistent

## Rule

After any change to tooling, code, structure, or process, check every
documentation surface in this repo for anything that now describes the old
state, and update it in the same change - don't leave it for later:

- `README.md` and `TUTORIAL.md`
- `CONTRIBUTING.md`, `MAINTAINERS.md`, `SECURITY.md`, and `CHANGELOG.md`
- `AGENTS.md` (the Prompts, Skills, Rules, and Repository references tables)
- `.agents/rules/*.md` and `.agents/skills/*/SKILL.md`
- `docs/`, and each project's own docs and `tests/README.md` under
  `coffeeAGNTCY/coffee_agents/{corto,lungo,recruiter}/`
- Comments inside scripts and workflow files that describe what something
  does or where it fits in a pipeline

## Why

A change that's correct can still leave the documentation lying: a stale
filename, an outdated count, a task that no longer exists, a rule that
still describes the old behavior. Nothing catches this automatically -
there's no linter for "this sentence is still true." Documentation that's
fallen behind is worse than no documentation, because it's trusted by
default until someone discovers otherwise.

## How to apply

- Grep the whole repo for the specific old name, value, count, or filename
  being replaced - not only the files already known to reference it.
- Re-read every surface in the list above that could plausibly mention what
  changed, even where a literal grep found nothing - a paraphrase or a value
  embedded in a code block won't always match a string search.
- If a change removes or renames something, confirm nothing still points at
  the old name: a markdown link, a task name in prose, an enum value quoted
  in a sentence, a file-tree diagram entry.
