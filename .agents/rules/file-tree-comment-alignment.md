---
name: file-tree-comment-alignment
description: >-
  In an ASCII file-tree diagram (e.g. a README's repository/source layout
  section), align every trailing '#' comment to the same column. Apply when
  writing or editing such a diagram; not automatically checked by any tool.
---

# File-tree comment alignment

## Rule

When a documentation file contains an ASCII file-tree diagram (a fenced code
block using `├──`/`└──`/`│` connectors, each line optionally followed by a
`#` comment describing that entry), pad every line so its `#` starts in the
same column - the widest entry (connector + path) plus one space sets the
column for the whole block.

## Why

A ragged comment column is harder to scan than one that lines up - the eye
has to hunt for where each comment starts instead of reading straight down
a column. This is purely a visual/documentation convention: there's no
linter for it, so it has to be applied by hand (or by an agent) whenever
such a block is written or edited.

## How to apply

- Recompute alignment for the **whole block** any time you add, remove, or
  rename an entry - a new longest line shifts every comment's column.
- Entries with no comment don't need trailing whitespace; only pad lines
  that actually have a `#` comment.
- This applies to any such diagram in the repo's documentation (e.g.
  [coffeeAGNTCY/coffee_agents/recruiter/README.md](../../coffeeAGNTCY/coffee_agents/recruiter/README.md)'s
  source-layout sections), not only the one that prompted this rule.

## Example

Before (ragged):

```
patterns/
├── example/ # skeleton
└── real-example/ # actual entry
```

After (aligned):

```
patterns/
├── example/       # skeleton
└── real-example/  # actual entry
```
