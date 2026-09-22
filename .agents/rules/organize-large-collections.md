---
name: organize-large-collections
description: >-
  When a flat, human-facing collection grows large enough that scanning it
  or finding one item takes real effort, group it into a light hierarchy or
  named categories - this includes the file system itself (subdirectories,
  filename prefixes), not only docs (a naming prefix, a table split into
  labeled sections). Default behavior unless context doesn't fit or a human
  says not to for that collection.
---

# Organize large collections

## Rule

When a flat, human-facing collection grows large enough that scanning it or
finding the one item that's actually needed takes real effort, look for a
natural way to break it into smaller, named groups rather than leaving it as
one long flat list. This applies equally to documentation collections (a
list of files, a set of tasks, a table, a set of options) and to the file
system itself - a directory that's accumulated many files is exactly as
much a "flat collection" as a long bullet list, and gets the same
treatment. A light hierarchy is enough - it doesn't need to be deep:

- **Subdirectories that group related files** - e.g. splitting
  `.agents/skills/` or `.agents/rules/` into subdirectories by concern once
  either grows past a size where a flat listing stops being scannable,
  reusing whatever section names `AGENTS.md`'s tables already grouped
  things under - when a discovery convention is documented in prose (skills
  as `.agents/skills/*/SKILL.md`), update that documentation to the new
  depth rather than leaving it stale.
- **A naming prefix/namespace** for things that can't be moved into
  directories (task names, script names).
- **A table split into labeled sections**, or a list broken into a few
  sub-bulleted groups with short headers, for documentation.

This is the default when nothing says otherwise - not a suggestion to apply
only when convenient. Skip it when the context genuinely doesn't fit
(there's no natural grouping, or forcing one would be more confusing than
the flat list) or when a human explicitly says not to for that collection;
either way, that's a deliberate, statable exception, not a silent one.

## Why

A human can hold a handful of items in mind at once without effort; past
that point, keeping track of a flat collection becomes real work, and
finding the one thing that's actually needed takes longer. Exactly where
that point falls depends on the collection - how similar the items look,
how often someone needs to pick one out - not a fixed count. Grouping
doesn't need to be elaborate - even a naming prefix or a couple of named
sub-sections turns "scan fifteen things" into "pick the right group of
three, then scan that," which is a much smaller task at the point someone's
actually using it.

## How to apply

- Judge before deciding: this kicks in once a collection has grown large
  enough that scanning it or telling its items apart takes real effort -
  not at a fixed count. Don't impose structure on something still small
  enough to read at a glance.
- Prefer a grouping that already exists or is obvious from the domain over
  inventing a new one - consistency with what's already there beats a
  locally "better" scheme.
- When a natural grouping doesn't exist, it's fine to conclude none should
  be forced - state that conclusion rather than leaving it unconsidered.
- If asked to add another item to a flat collection that's already
  borderline hard to scan, that's the moment to raise whether it's time to
  group it - not something to defer indefinitely one item at a time.
- Design a new grouping with room to grow, not just to fit what exists
  right now - a category sized for one item today is fine if it's a
  genuinely distinct concern that others will join later.
- Moving files is the easy part; finding and fixing every reference to
  their old path is the actual work - grep the whole repo (scripts calling
  each other, docs, workflow files) rather than trusting memory of who
  references what, and verify by actually running the moved thing
  afterward, not just by reading the diff.
