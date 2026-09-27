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
- ~~Retrofitting tests onto any of the ~20 pre-existing scripts~~ -
  **done as an immediate follow-up, not deferred indefinitely**: every
  script that existed anywhere in the repository when this rule was
  introduced now has a real test (151 tests total), including
  `coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh` - the
  `NOT_YET_TESTED` allow-list is empty. What stays a non-goal is
  automating *quality* judgment about any given test - see below.
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

**`bats-core`, installed from its own GitHub source tarball, not the
`bats` npm package or a shell/Python test framework.** The npm package was
this design's first draft, reasoning that reusing `openspec`'s exact `npm
install --global --prefix .tools` recipe meant zero new install *shape* to
build. Revisited once the question came up directly: is Node actually
necessary here? Checking confirmed `bats-core` has no Node dependency at
all - the npm package is a pure convenience wrapper - while `@fission-ai/openspec`
genuinely is a Node application (real `dependencies` in its own
`package.json`: `commander`, `inquirer`, `zod`, ...; no compiled/standalone
release asset on GitHub either). So Node stays, but only for `openspec`;
routing `bats` through npm/Node too was an unforced, unnecessary coupling
- a Node bootstrap failure would have broken `bats` as a side effect, for
a tool that has nothing to do with Node. `bats-core`'s own tagged source
tarball ships an `install.sh <prefix> [libdir]` that creates
`<prefix>/{bin,libexec/bats-core,lib/bats-core}` - verified locally
(downloaded v1.13.0, ran `install.sh` into a throwaway prefix, confirmed
`bin/bats --version` works from that relocated path). Like `node`, this
means `bats` gets its own `.tools/bats/` directory rather than joining the
flat `.tools/bin/`, since it isn't a single relocatable binary either -
see the Migration Plan below.

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

**The coverage audit was a hardcoded "not-yet-tested" allow-list during
the backfill, removed once it emptied out - it is not a permanent
mechanism.** While the backfill was in progress, its shape mirrored
`check_pipeline_exceptions.bash`'s own "Known exceptions" list: a bash
array in the script, a comment pointing at where to keep it in sync, and
a failure that named anything found outside it - so the remaining gap was
visible and shrank one line at a time rather than either silently
allowing untested scripts forever, or failing CI immediately for a
decision the user had made on purpose ("fix the gaps later"). Once every
script had a real test, the user asked for the allow-list itself to be
removed entirely rather than kept empty as a mechanism future scripts
could quietly be added to - the check is now a flat "every script needs a
test, no exceptions" gate, with no array, no override variable, and no
per-script escape hatch at all.

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
  did not materialize, and no longer can: the backfill happened
  immediately as a follow-up (see Migration Plan), and the allow-list
  mechanism itself was then removed entirely rather than kept around
  empty - there's nothing left to forget.
- [A hand-rolled `mock_command` helper has some rough edge a real mocking
  library would have already solved] -> low stakes: it's a few lines
  behind its own unit test (see Migration Plan), and can be replaced by
  the two reference examples' usage patterns without touching every future
  test file's syntax, since they only ever call `mock_command`, never a
  library-specific API.
- [GitHub's auto-generated source tarball for a tag changes shape or
  disappears] -> same trust model this repo already extends to every
  other tarball-installed tool (`actionlint`, `shellcheck`, `shfmt`,
  `task`); `bats-core` tags aren't going to stop having one, since it's
  the standard GitHub archive URL, not a custom release asset.

## Migration Plan

Add `BATS_VERSION` to `scripts/lib/versions.sh` and an install block to
`scripts/setup.sh` (tarball + `install.sh` into `.tools/bats/`, not npm);
add `.tools/bats/bin` to `scripts/env.sh`'s `PATH`; write
`scripts/lib/testing.sh`; write the two reference example test files;
write the coverage-audit script with today's full script inventory as its
allow-list; add `tests:bash`/`tests:coverage` Taskfile tasks; wire both
into `scripts/checks/check_all.bash`; add the skill and rule; index both
in `AGENTS.md`. Purely additive - no existing script's behavior changes
(the `bats` install path is new, not a change to an existing tool).
Rollback is a plain `git revert`.

**Follow-up (same change, done immediately rather than deferred):**
broadened the rule and `check_bash_test_coverage.bash`'s scan from
`scripts/` to the whole repository (finding exactly one other script,
`coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh`); wrote a
real test for every one of the ~16 scripts under `scripts/` that predated
the rule. That script was initially grandfathered instead, on the
reasoning that it's the subject of its own separate, already-planned
refactor on a stashed branch and testing its current shape would be
wasted effort - revisited on the user's explicit request and tested for
its current shape anyway (16 tests, using the same fixture-copy technique
as the other executable scripts, with `dirctl` mocked), emptying
`NOT_YET_TESTED` entirely. No bugs were found in any of the 17 scripts
under test - every test confirmed existing behavior rather than catching
a regression. One unrelated, pre-existing finding surfaced while
hardening `check_bash_test_coverage.bash` for an empty `NOT_YET_TESTED`
array (a `set -u`-safe `"${arr[@]:-}"` fix, needed since macOS's system
`/bin/bash` is still 3.2 and errors on expanding a genuinely empty array
under `nounset`): that same `/bin/bash` also lacks `mapfile` entirely
(introduced in bash 4.0), which every `check_*.bash` script already
depends on - a repo-wide pre-existing bash-3.2 incompatibility, not
something this change introduced or fixes.

**Follow-up (CI failure on the GitHub-hosted Ubuntu runner, not caught
locally on macOS):** `scripts/lib/tests/fetch.bats` simulated "curl/wget/
sudo/apt-get/id absent" by restricting `PATH` to `$MOCK_BIN_DIR:/bin`,
reasoning (stated in its own comment at the time) that those tools "never
live in bare /bin" on macOS. That's true on macOS, where `/bin` is a
small, separate directory - but false on Debian/Ubuntu's merged-usr
layout, where `/bin` is a symlink to `/usr/bin`, so the real tools stayed
reachable and 6 tests failed on CI while passing locally. Fixed by adding
`mock_isolate_path` to `scripts/lib/testing.sh`: instead of guessing a
system directory believed not to contain a tool, it symlinks (not
copies - a `cp` of a macOS system binary elsewhere gets killed by
code-signing enforcement on exec, while a symlink still resolves to, and
passes signature verification against, the original file) each
explicitly-named tool into the mock bin directory from the *original*
PATH, then restricts PATH to *only* that directory - portable by
construction, since it never depends on which real directory happens to
contain what. Also removed `mock_command`'s own dependency on external
`cat` (rewritten with `echo` instead, both bash builtins), since a test
isolating PATH down to just what it explicitly names would otherwise also
need to keep `cat` reachable purely for `mock_command`'s own sake.

**Follow-up (removing the allow-list mechanism entirely, on explicit
request):** with the backfill complete and `NOT_YET_TESTED` empty,
keeping the mechanism around (even empty) would have meant a future
script could quietly be added to it instead of getting a real test - the
user asked to close that door rather than leave it available. Removed
`NOT_YET_TESTED`, `NOT_YET_TESTED_EXTRA`, and `is_grandfathered` from
`check_bash_test_coverage.bash` entirely; the check is now unconditional:
any script without a test fails, full stop. Updated its own test
(dropped the "explicitly grandfathered" case, kept the "has a test" and
"fails when it doesn't" cases) and every doc that described the allow-list
as a live mechanism (the rule, the skill, `CONTRIBUTING.md`,
`Taskfile.yaml`) to describe it only as something the backfill used
temporarily, not something that still exists.
