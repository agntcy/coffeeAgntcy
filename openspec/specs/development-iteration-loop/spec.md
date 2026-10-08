# development-iteration-loop Specification

## Purpose
Requires a substantial change in this repo to follow an explicit
ideate/design/implement/review/document loop, with review run after every
step (looping back on failure) and documentation notes tracked from the
first step onward, rather than review and documentation each happening
only once, at the end.

## Requirements

### Requirement: A substantial change follows the five-step loop
A substantial change (the same threshold `plan-with-openspec` uses: a new
tool/script/CI check, a schema or repo-wide convention change, or anything
spanning more than a small, self-contained diff) SHALL proceed through
five steps in order - ideate, design, implement, review, document - rather
than jumping straight to implementation.

#### Scenario: Starting a substantial change
- **WHEN** work begins on a change that meets the substantial-change
  threshold
- **THEN** the change proceeds through ideate, design, implement, review,
  and document, in that order

#### Scenario: Starting a small, self-contained change
- **WHEN** work begins on a change that does not meet the substantial-change
  threshold (a bug fix, a small doc update, a single self-contained script)
- **THEN** the normal PR flow applies, with no separate loop required

### Requirement: Review runs after every step, with loop-back on failure
Each of the ideate, design, and implement steps SHALL be reviewed before
moving to the next step, using the same criteria
`self-review-after-change` already defines. A review that finds a problem
SHALL cause the change to return to the step that owns the problem (or an
earlier one it depends on) and repeat from there, rather than proceeding
with a known issue.

#### Scenario: A step's review finds no issue
- **WHEN** a step's output is reviewed and no issue is found
- **THEN** the loop proceeds to the next step

#### Scenario: A step's review finds an issue
- **WHEN** a step's output is reviewed and an issue is found
- **THEN** the loop returns to the step that owns the issue (or an earlier
  step it depends on), the issue is fixed, and that step's review runs
  again before the loop proceeds

### Requirement: Documentation notes accumulate from the first step
Documentation-relevant notes (what will need to be updated in the repo's
documentation surfaces per `keep-docs-consistent`) SHALL start being
tracked at the ideate step and accumulate through design and implement,
rather than being reconstructed from scratch at the document step.

#### Scenario: The document step runs
- **WHEN** the loop reaches the document step
- **THEN** it reconciles the documentation-relevant notes already
  accumulated since the ideate step against the repo's current state,
  rather than starting that discovery from nothing

### Requirement: Implementation includes automated tests unless infeasible
A code change made during the implement step SHALL be accompanied by
automated tests added in the same step, unless doing so is infeasible -
a judgment call, using the same bar `bash-script-testing` already applies
within its own domain (bash scripts), generalized to any code change.

#### Scenario: A code change ships with tests
- **WHEN** the implement step makes a code change that can feasibly be
  tested
- **THEN** automated tests covering that change are added in the same step

#### Scenario: A code change has no feasible test
- **WHEN** the implement step makes a code change for which an automated
  test is genuinely infeasible
- **THEN** the change proceeds without one, and the reason is recorded as
  a judgment call rather than silently skipped
