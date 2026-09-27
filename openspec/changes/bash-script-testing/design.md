# Design

## Context

See `proposal.md` for the motivation. This repo's own `scripts/` tree
splits cleanly into two kinds of file, and that split is what makes
"introduce testing without retrofitting anything" possible at all:

- **Shared libraries** (`scripts/lib/*.sh`) are always `source`d by
  another script, never executed directly - `setup.sh` already does
  `source "$SCRIPT_DIR/lib/versions.sh"` etc. A `.bats` file can `source`
  the same file and call its functions directly, with no change to the
  library itself.
- **Executable scripts** (`scripts/checks/*.bash`, `scripts/lint/*.bash`,
  `scripts/ci-gate/*.sh`, `setup.sh`) are already meant to be run as a
  whole process, invoked by a Taskfile task or CI. `bats`'s `run` helper
  executes exactly that same subprocess in a test, with no change to the
  script either.

Neither kind needs restructuring (no `main()` guard, no new sourcing
convention) to become testable - which is why this proposal can introduce
the requirement without opening the "retrofit ~20 scripts" project it
explicitly defers.

## Goals / Non-Goals

**Goals:**
- A new shared library or executable script added from now on is expected
  to ship with tests in the same change, and a coverage audit catches one
  that doesn't.
- Two real, working reference examples exist (not throwaway toy scripts),
  proving both test shapes against actual existing code with zero changes
  to that code.
- Every script that predates this rule keeps working exactly as before;
  none of them are touched by this change.

**Non-Goals:**
- Retrofitting tests onto any of the ~20 pre-existing scripts - explicitly
  deferred, tracked as the coverage audit's own hardcoded gap list (see
  Decisions).
- Enforcing test *quality* ("thorough") by automation - not machine
  checkable, same as this repo already accepts for `pin-exempt`'s
  "genuine reason" or a rule's own judgment-call exceptions. Covered by
  `self-review-after-change`/`pre-finalize-checks` and normal review
  instead.
- Adopting `bats-support`/`bats-assert` or any other bats plugin - see
  Decisions below.
- Restructuring any existing script's internals (e.g. extracting more
  functions to make more of it unit-testable) - a real, valuable future
  improvement, but its own separate change, not bundled into introducing
  the convention.

## Decisions

**`bats-core`, installed via the official `bats` npm package, not a
git-cloned tarball or a shell/Python test framework.** This repo already
bootstraps a pinned Node.js solely to install `openspec` the same way;
reusing that exact `npm install --global --prefix .tools bats@<version>`
recipe means zero new install *shape* to build (`setup.sh` gains one more
block that looks like every other npm-installed tool it already has), and
`bats` (not a fork or a bespoke bats-core packaging) is the framework's own
official npm distribution, actively maintained by the bats-core team
itself.

**No `bats-support`/`bats-assert` plugin.** Both are popular companion
libraries for nicer assertion messages, but adding either means either a
second npm dependency or a git submodule/vendored copy - more pinned
surface for a benefit (prettier failure output) this repo's own hand-rolled
check scripts already do without elsewhere (`check_pinned_references.bash`
etc. have no assertion library either, just `echo` and a `failed` flag).
Bats' built-in `run`/`[ "$status" -eq 0 ]`/`[ "$output" = "..." ]` primitives
are enough; revisit only if writing tests without them turns out to be
genuinely painful in practice.

**A hand-rolled `mock_command` helper (`scripts/lib/testing.sh`), not a
mocking library.** Mocking here just means "put an executable stub ahead of
the real binary on `PATH` for one test" - a few lines of bash (write a
small script to a temp dir, `chmod +x`, prepend that dir to `PATH`, restore
`PATH` in teardown). A dedicated mocking library (e.g. `bats-mock`) would
be one more pinned dependency for a problem this repo can solve directly,
consistent with the "no bats-assert either" decision above.

**Test files live in a `tests/` subdirectory next to what they test**
(`scripts/lib/tests/`, `scripts/ci-gate/tests/`, `scripts/checks/tests/`,
`scripts/lint/tests/`), not a single top-level `scripts/tests/` mirroring
the tree. Consistent with this repo's own `organize-large-collections`
default (group by concern, and a script's tests are that script's own
concern) and keeps a `.bats` file's relative `load` path to
`scripts/lib/testing.sh` short and uniform
(`scripts/<category>/tests/*.bats` is always exactly two levels above
`scripts/`).

**The coverage audit is a hardcoded "not-yet-tested" allow-list that
shrinks over time, not a hard "every script needs tests today" gate.**
Identical shape to `check_pipeline_exceptions.bash`'s own "Known
exceptions" list: a bash array in the script, a comment pointing at where
to keep it in sync, and a failure that names anything found outside it.
Here the array starts as literally every script that exists before this
change (the deferred backfill's own punch list), and the audit fails the
moment a *new* script shows up without a test and without being added to
that list - so the gap is visible and shrinks one line at a time as the
follow-up work happens, rather than either (a) silently allowing untested
scripts forever, or (b) failing CI today for a decision the user already
made ("fix the gaps later").

**Unit tests only apply to `scripts/lib/*.sh`, not to functions inside an
executable check script.** Several check scripts do define a helper
function (e.g. `check_pinned_references.bash`'s `check_exempt`), and
sourcing the whole file to unit-test just that function is possible in
principle - but every one of those files runs its top-level scanning logic
immediately after its function definitions, with no guard, so `source`ing
one for its function would also execute the entire check against whatever
directory the test happens to run in. Making that safe needs a `main()`
guard convention this proposal explicitly isn't retrofitting onto existing
scripts (see Non-Goals). A *new* executable script could adopt a guard and
get real unit tests for its own functions in addition to a mocked e2e
test - this rule doesn't forbid that, it just doesn't require it, since a
mocked e2e test (which needs no guard at all) already covers the same
logic path by path.

## Risks / Trade-offs

- [The "not-yet-tested" allow-list is forgotten and never shrinks] ->
  acceptable for this change: the list existing and being enforced (a new
  script can't join it silently) is strictly better than no list, and
  shrinking it is explicitly the user's own planned follow-up, not
  something this change can force by itself.
- [A hand-rolled `mock_command` helper has some rough edge a real mocking
  library would have already solved] -> low stakes: it's a few lines
  behind its own unit test (see Migration Plan), and can be replaced by
  the two reference examples' usage patterns without touching every future
  test file's syntax, since they only ever call `mock_command`, never a
  library-specific API.
- [`bats` (the npm wrapper) drifts from upstream `bats-core` releases] ->
  same trust model this repo already extends to `@fission-ai/openspec`
  (also an npm-distributed CLI); revisit only if a version gap actually
  causes a problem.

## Migration Plan

Add `BATS_VERSION` to `scripts/lib/versions.sh` and an install block to
`scripts/setup.sh`; write `scripts/lib/testing.sh`; write the two
reference example test files; write the coverage-audit script with today's
full script inventory as its allow-list; add `tests:bash`/`tests:coverage`
Taskfile tasks; wire both into `scripts/checks/check_all.bash`; add the
skill and rule; index both in `AGENTS.md`. Purely additive - no existing
script changes. Rollback is a plain `git revert`.
