---
name: no-em-en-dashes
description: >-
  Never use an em dash (Unicode U+2014) or en dash (U+2013) anywhere in this
  repo - prose, code comments, commit messages, generated output. Always use
  a plain ASCII hyphen (-) instead. Enforced by the "Forbidden strings" job
  in .github/workflows/source-lint.yaml.
---

# No em dashes or en dashes

## Rule

Never write an em dash (Unicode U+2014) or en dash (U+2013) anywhere in this
repo - documentation, code comments, commit messages, script output,
anything. Always use a plain ASCII hyphen (U+002D, the `-` key) instead,
with spaces around it where you'd otherwise reach for a dash as a
parenthetical separator (`text - like this - continues`, not
`text-like this-continues`).

This file deliberately never shows the literal characters it's describing -
they're named by Unicode code point instead, so this file itself doesn't
trip the very check it documents.

## Why

A repo with many contributors and agents, each with their own default
writing style, drifts toward inconsistent typography unless something holds
the line. An ASCII hyphen renders identically everywhere - every terminal,
every diff viewer, every font - and matches byte-for-byte in a grep, whereas
an em dash or en dash can look nearly identical to a hyphen in some fonts
while being a completely different byte sequence, silently breaking
exact-string search and producing invisible inconsistency across files.

## How to apply

- Before finalizing any text you write in this repo, scan it for U+2014 and
  U+2013 and replace both with a plain hyphen.
- To check the whole repo (bash's `$'\uXXXX'` form takes a Unicode code
  point, not a literal character, so this file never has to show one):
  `scripts/check_forbidden_strings.bash --pattern $'\u2014' --pattern $'\u2013'`.
  To fix violations in place instead of by hand:
  `scripts/find_strings.bash --pattern $'\u2014' --pattern $'\u2013' --replace-with '-' --write`.
- CI enforces this on every push/PR: the "Forbidden strings" job in
  [.github/workflows/source-lint.yaml](../../.github/workflows/source-lint.yaml)
  runs the same check via the
  [check-forbidden-strings](../../.github/actions/check-forbidden-strings/action.yaml)
  composite action.
