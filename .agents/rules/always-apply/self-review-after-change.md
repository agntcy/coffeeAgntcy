---
name: self-review-after-change
description: >-
  After making a change, review it against the original requirements,
  repo-wide consistency (docs/rules/skills/config that reference what
  changed), compliance with every rule currently in .agents/rules/ (not only
  the ones the change obviously touches), general repo consistency and
  integrity beyond just what changed, and common practices - not just
  automated checks. Apply as the final step of any change.
---

# Self-review after a change

## Rule

After making a change - before treating it as finished - review it against
five things deliberately, not just by running automated checks:

1. **Requirements** - re-read what was actually asked and confirm the
   change does all of it, not just the first interpretation reached for.
   Check for scope creep in either direction: something asked for but
   skipped, or something changed that wasn't asked for.
2. **Repo consistency** - search for anything else in the repo that
   references what changed (a filename, a value, an enum, a task name, a
   count) and update every one of them, not only the files already
   touched. `AGENTS.md`'s tables are where this drifts most often.
3. **Rule compliance** - go through every rule currently in
   `.agents/rules/`, not only the ones the change obviously relates to, and
   check the repo still complies with each. A change can be correct on its
   own terms and still leave an older, unrelated rule newly violated (e.g. a
   file move that orphans a rule's own cross-reference, or a new item that
   tips a collection over a size/organization threshold).
4. **General repo consistency and integrity** - beyond the specific things
   the change touched, sanity-check the repo as a whole: does `AGENTS.md`
   still match the filesystem exactly, do all backtick-quoted and
   markdown-style paths still resolve. Don't scope this only to what you
   just edited - a broader change (a rename, a reorg) can surface staleness
   that predates it.
5. **Common practices** - does the change hold up against general good
   practice for its kind (clear naming, no unjustified duplication,
   sensible defaults, not reinventing something the repo already has a
   mechanism for) - not only against this repo's own specific rules.

## Why

Automated checks verify mechanical properties, but they can't tell you
whether the task was actually finished, whether other files still say the
old thing, whether an unrelated rule quietly broke, or whether the approach
itself is sound. A change can pass every automated check while still being
incomplete, contradicting itself elsewhere in the repo, silently violating a
rule nobody thought to re-check, or technically correct but not how anyone
would actually choose to do it. Scoping the review only to "what did I just
touch" misses drift a rename, reorg, or rebase can surface in files the
change never opened.

## How to apply

- Do this after any automated checks pass, not instead of them - this rule
  covers the judgment layer, not the mechanical one.
- Re-read the original request verbatim and check off each part
  explicitly, rather than trusting memory of what was done.
- Grep the repo for the specific old value/name/count being replaced, not
  only the files already remembered as touched.
- For rule compliance: list every file under `.agents/rules/` and go
  through each - most of these are judgment calls or audits with no script
  to run, so they need an actual read against the current state, not just a
  memory of having satisfied them once.
- For general integrity: verify `AGENTS.md`'s tables list exactly what's on
  disk and nothing else (a stale or missing row in either direction), and
  that every backtick-quoted or markdown-linked path in the repo still
  resolves.
- If something looks inconsistent or incomplete during this review, fix it
  as part of the same change - don't leave it for a future pass.
