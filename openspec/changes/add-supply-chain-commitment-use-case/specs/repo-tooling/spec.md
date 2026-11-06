# Spec Delta

## MODIFIED Requirements

### Requirement: Dashes are checked and fixable
`task dashes:check` SHALL scan the repo for an em dash (U+2014) or en
dash (U+2013) and report every hit by file and line, without modifying
any file. `task dashes:fix` SHALL replace every such hit with a plain
ASCII hyphen in place. Both SHALL skip vendored third-party directories
named `third_party`, whose content must stay identical to its upstream
source.

#### Scenario: A dash is present
- **WHEN** `task dashes:check` is run against a repo containing an em
  dash or en dash anywhere in a tracked or untracked, non-ignored file
  outside a `third_party` directory
- **THEN** it reports that file and line, and exits non-zero

#### Scenario: A dash is present in vendored third-party content
- **WHEN** `task dashes:check` or `task dashes:fix` is run and the only
  em dash or en dash is inside a `third_party` directory
- **THEN** the check exits zero and the fix leaves that file unchanged
