---
name: alphabetize-entity-lists
description: >-
  Keep a bulleted, itemized, or tabular list alphabetically ordered when its
  items (or, for a table, its key column) are entities (names, files, tags,
  terms) rather than full sentences. Two exceptions: full-sentence bullets
  (or table rows whose key column is itself a long descriptive phrase) keep
  their original order, and in-code entity lists with a deliberate logical
  order need to ask first - and whenever an exception applies, leave a note
  explaining why. Apply whenever writing or editing such a list.
---

# Alphabetize entity listings

## Rule

When a list's items are entities - bare names, filenames, tags, terms,
single short phrases with no attached explanation - keep them in
alphabetical order. This applies to markdown bullet lists, to itemized
lists in code/config (e.g. a YAML array of tags), and to markdown table rows
keyed by a bare-entity column - sort the table by that column, even when
another column carries a full sentence of explanation. It does not apply to
numbered/sequential lists (numbering itself signals that order matters) or
file-tree diagrams
(`.agents/rules/file-tree-comment-alignment.md` already governs those).

There are two exceptions:

1. **Full sentences.** If a list's items are full sentences, an entity name
   followed by an explanatory clause (e.g. `` `proof/` - evidence from test
   runs... ``), or - for a table - the row's own key column is itself a
   long descriptive phrase rather than a bare name (e.g. an error-message
   pattern, not a short label), keep them in their original order - order
   there usually carries meaning (narrative flow, sequence, priority, "most
   common case first") that alphabetizing would destroy. This case is
   self-evident from the content itself, so it doesn't need a note (see
   below) - nobody mistakes a paragraph-length bullet, or a table keyed by
   long phrases, for an alphabetizable list.
2. **In-code entity lists with a deliberate logical order.** An enum whose
   values are meant to be read as a sequence (e.g. a lifecycle: `Draft ->
   Review -> Approved`), or fields/properties in a conventional order (e.g.
   `[username, password]`), may already be ordered for a reason other than
   alphabetical. Don't silently alphabetize these - ask the person you're
   working with whether to reorder, and go with whatever they decide.
   Remember that decision for the same list going forward, so it isn't
   re-asked every time the list is touched - see "Leaving a note" below for
   how.

## Leaving a note

Whenever a list is kept in its original/definition order under exception 2
(a real judgment call, not self-evidently sequential prose), leave a
visible trace of that decision at the point of use, in whichever form the
file format allows:

- **Code comment**, right next to the list, in any format that supports one
  (shell, YAML, workflow files).
- **Explicit inline note**, in prose or in a field that already carries
  descriptive text, when there's no comment syntax available (plain JSON
  has none).
- **A line in this rule's "Decided exceptions" log** below, when neither of
  the above fits cleanly at the location itself (e.g. a JSON object's own
  key order, which has nothing to attach a note to).

Use more than one of these when it helps; use at least one.

## Decided exceptions

Judgment calls already made, so they aren't re-litigated or accidentally
"fixed" later. None recorded yet - add an entry here (or an inline note at
the point of use) the first time exception 2 is invoked.

## Why

An alphabetically ordered list of entities is faster to scan and to diff -
a reader can jump straight to the item they're looking for, and adding one
new item produces a single-line diff instead of shuffling the whole list.
That benefit doesn't apply to sentences (where sequence *is* the content) or
to code where order is already meaningful (enum values, positional fields)
- alphabetizing those would be actively wrong, which is why they're carved
out rather than treated as a lower-priority version of the same rule.
Leaving a note at each exception exists so a future editor (or agent)
doesn't rediscover the same question, or "helpfully" alphabetize something
that was deliberately left as-is.

## How to apply

- Before alphabetizing an existing list, classify it first: bare entities
  (alphabetize), sentences or entity-plus-explanation (leave as-is, no note
  needed), or in-code with plausibly intentional order (ask first, then
  note the decision either way).
- For a table, classify by its key column specifically, not the row as a
  whole: a bare name/term key (alphabetize the table by it, regardless of
  how long any other column's text is) versus a key that's itself a long
  descriptive phrase (leave the table's order as-is, same as a
  full-sentence bullet list).
- When adding a single new item to an already-alphabetized entity list,
  insert it in the correct alphabetical position rather than appending it
  at the end.
- When unsure whether an in-code list's order is deliberate, treat it as
  exception 2 and ask, rather than guessing either way.
- When retroactively applying this rule to existing lists, also
  retroactively add the missing note for any exception-2 case that doesn't
  already have one - don't leave a silent exception standing.
