# Proposal

## Why

Releases in this repo ship whenever a milestone is done, so their dates
drift (0.3.0 in August, 0.4.0 late September, the next one planned for
2026-10-29) and nobody outside the maintainers can tell ahead of time
when the next version lands or what it will contain. `CHANGELOG.md`'s
`Unreleased` section is a placeholder (`.`), and each version's entry is
written only at release time from the commit history, so planned and
already-merged work is invisible until the day a version is cut.

Moving to a fixed monthly cadence, with each month's release carrying a
code name, gives a predictable ship date and a stable name to point at,
and keeping `Unreleased` current in every PR makes the next release's
content visible while it is being built.

## What Changes

- **Monthly cadence.** Each month has one release, cut on the last day of
  the month. The three days before cut day are the freeze: a version
  merged and tagged before the freeze starts ships in that month's
  release, and anything later rolls into the next month.
- **Named releases.** Each monthly release keeps the code name of its
  GitHub milestone (Heartbeat, Fiber, Synapsis, Cerebro, and next Nexus),
  now paired with the month it ships in, e.g. "Nexus (October 2026)". A
  milestone's due date is the last day before its month's freeze.
- **Independent versions.** Versions stay Semantic Versioning, are cut
  only when there is something to ship, and are tagged without a `v`
  prefix as today. A month with nothing to ship has no new version.
- **`Unreleased` kept current.** `CHANGELOG.md`'s `## Unreleased` section
  starts with a `Target: <version> - <date>` line and lists what the next
  version will contain under Keep a Changelog headings. Any user-visible
  PR adds its entry in the same PR; planned, unmerged work is marked
  `(planned)`.
- **Released entries keep today's format.** At cut, the
  `generate-release-notes` skill turns `Unreleased` into the detailed
  version section it already produces (summary dropdowns, dependencies,
  changeset, contributors), now with a `Release: <Code name> (<Month
  YYYY>)` line under its heading. Earlier entries are left untouched.
- **New always-apply rule `keep-changelog-current`**, so agents add the
  `Unreleased` entry in the same change as any user-visible change.
- **Docs:** a "Releases" section in `CONTRIBUTING.md` holding the policy;
  `docs/RELEASE-OPS.md` steps aligned with it; the README milestones table
  becomes a releases table mapping each code name to its month and
  version; a "Changelog" section in the PR template; `AGENTS.md`,
  `keep-docs-consistent` and `repo-operation-pipeline` list the new rule.

## Capabilities

### New Capabilities

- `release-process`: the monthly named-release cadence, freeze and cut
  rules, versioning and tagging, the `Unreleased` upkeep contract in
  `CHANGELOG.md`, and how a version's released entry is produced and
  labeled with its named release.

### Modified Capabilities

None.

## Impact

- Docs and agent instructions: `CHANGELOG.md`, `CONTRIBUTING.md`,
  `docs/RELEASE-OPS.md`, `README.md`, `.github/pull_request_template.md`,
  `AGENTS.md`, the release-notes prompt files and skill, and the
  always-apply rules.
- One script line: the new rule joins the rule-only exceptions listed in
  `repo-operation-pipeline.md` and in
  `scripts/checks/check_pipeline_exceptions.bash`'s `RULE_ONLY_EXCEPTIONS`,
  which must stay in sync.
- No tasks, CI workflows, application code, Helm charts or tag scheme
  change.
- The `Nexus` milestone's due date (2026-10-29) falls inside the October
  freeze and needs moving to 2026-10-27 on GitHub; that is a manual step
  outside this change.
