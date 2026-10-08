# Design

## Context

The repo already has a working release process (see proposal.md - Why
for what it lacks):

- `docs/RELEASE-OPS.md` is the maintainer runbook: audit Helm chart
  bumps, close the milestone and open the next `(current release)` one,
  generate notes, merge a release PR, sign and push a tag, wait for CI,
  publish the GitHub release, update deployments.
- The `generate-release-notes` skill writes a detailed `CHANGELOG.md`
  section (summary dropdowns, migration steps, dependencies, changeset,
  contributors) that is reused verbatim as the tag annotation and the
  GitHub release body.
- Milestones carry code names (Heartbeat, Fiber, Synapsis, Cerebro,
  Nexus), and GitHub release titles follow `<tag> - <Milestone>
  (<YYYY-MM-DD>)`. Tags have no `v` prefix.
- `CHANGELOG.md`'s `## Unreleased` holds a single `.` placeholder.
- The README milestones table stops at Synapsis and lists intended months
  that no longer match what shipped.

## Goals / Non-Goals

**Goals:**

- Keep the existing runbook, tag scheme, release-notes format and
  milestone code names, and add the cadence on top of them.
- One written place for the release policy (`CONTRIBUTING.md`,
  "Releases"), linked from the runbook rather than repeated in it.
- Docs that make sense to a reader of this repo alone.

**Non-Goals:**

- A fixed, pre-agreed list of future code names. Names keep being chosen
  when a milestone is created, as today.
- Rewriting earlier `CHANGELOG.md` entries or retrofitting `Release:`
  lines onto versions that predate the cadence.
- Automating any of it. Whether a change is user-visible is a judgment
  call, and the freeze date is simple date arithmetic.
- Changing the GitHub milestone itself; moving Nexus's due date is a
  manual step for a maintainer.

## Decisions

- **The code name is the milestone name, paired with the month.** The
  repo already names releases through milestones, so the monthly release
  reuses that name instead of introducing a second naming scheme.
  Writing it as `Nexus (October 2026)` makes the ship month readable
  without a lookup. Alternatives: month-only names (drops a naming habit
  contributors already use and that the GitHub releases show), or a fixed
  alphabetical list (a new convention with no history in this repo).
- **Detailed released entries stay; only `Unreleased` changes shape.**
  The history is in the detailed format, and the runbook reuses that text
  for the tag annotation and GitHub release. `Unreleased` uses Keep a
  Changelog headings because it is written a PR at a time, where short
  categorized bullets are what a contributor can add without regenerating
  anything. At cut, the skill reads `Unreleased` as the authoritative list
  of what the version contains and expands it into the detailed format.
  Alternative: switch the whole file to Keep a Changelog and move the
  detailed text to the GitHub release only, rejected because it breaks the
  file's existing shape and the runbook's reuse of the entry.
- **`## Unreleased` keeps its current heading,** without Keep a
  Changelog's brackets, to match the repo's `## <version> (<date>)`
  headings.
- **Freeze is the three days before the last day of the month.** Cut day
  is fixed and needs no lookup; three days is enough to finish the
  release PR and tag after the last feature merges. "Merged and tagged
  before the freeze" is the inclusion test, so the whole runbook up to
  publishing the GitHub release happens before the freeze starts.
- **Milestone due date is the last day before the freeze.** It is then
  the latest possible target date, and the runbook's milestone step
  already sets dates, so this only fixes which date.
- **A code name follows its content, not the calendar.** If a milestone
  isn't ready by the freeze, it and its code name move to the next month.
  A month with nothing to ship therefore has no named release in this
  repo, which matches "no version just because a month passed".
- **Every version gets a `Release:` line,** patch versions included.
  Before, patch releases (0.1.1, 0.2.1) had no code name in their GitHub
  release title; now the title always carries the release it ships in.
- **The README milestones table becomes the releases table.** It already
  maps milestones to versions and dates, so it gains a month column and
  real values instead of a separate file listing releases.
- **Planned entries carry no reference.** A `(planned)` entry gets the
  PR number only once the PR exists, the same as any other entry.
- **Rule-only enforcement.** `keep-changelog-current` is a judgment-call
  rule, a documented exception in `repo-operation-pipeline.md`'s terms,
  added to `repo-operation-pipeline.md`'s "Known exceptions" list and the
  matching `RULE_ONLY_EXCEPTIONS` array in
  `check_pipeline_exceptions.bash`, so `pipeline:check-exceptions` would
  flag it if it ever gains a skill of its own.
  `self-review-after-change.md` needs no edit: it tells the reviewer to
  walk every file under `.agents/rules/` rather than naming them.
- **The first target is 0.5.0 on 2026-10-27.** The planned Nexus content
  (SLIM 2.0, A2A 1.0) includes interface-level upgrades, which a `0.x`
  version bumps by minor. 2026-10-27 is the last day before the October
  freeze (2026-10-28 to 2026-10-30, cut 2026-10-31).

## Risks / Trade-offs

- [Contributors forget the `Unreleased` entry] -> The PR template's new
  Changelog section asks for it, and the agent rule covers agent-written
  changes. The release-notes skill still diffs PRs since the last tag, so
  a missing entry shows up as a mismatch at cut time.
- [The Nexus milestone keeps its 2026-10-29 due date] -> The proposal's
  Impact names the manual fix; until then the README table and
  `Target:` line give the correct date.
- [Detailed and short formats in one file] -> The boundary is fixed:
  only `Unreleased` is short, and the cut replaces it whole.

## Migration Plan

Docs-only. The process takes effect when this change merges: the current
Nexus milestone becomes the October 2026 release, and its release PR is
the first one written with a `Release:` line. Rollback is reverting the
docs; no tag, workflow or artifact depends on them.
