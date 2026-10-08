# Spec Delta

## Purpose

Lets anyone see when the next coffeeAgntcy version ships, which named
monthly release it belongs to, and what it contains or is planned to
contain, without reading the commit history.

## ADDED Requirements

### Requirement: Monthly named releases

The repo SHALL ship releases on a monthly cadence. Each month's release
SHALL be cut on the last day of the month (its cut day), and the three
days before cut day SHALL be its freeze. Each monthly release SHALL carry
the code name of its GitHub milestone, written together with its month as
`<Code name> (<Month YYYY>)`, and the milestone's due date SHALL be the
last day before that month's freeze.

#### Scenario: Reader looks up a release

- **WHEN** someone wants to know which version shipped in a named release
- **THEN** the README's releases table maps each code name to its month,
  its version and its date

#### Scenario: Next milestone is opened

- **WHEN** a version ships and the next `(current release)` milestone is
  created
- **THEN** the milestone has its code name and a due date on the last day
  before the next month's freeze

### Requirement: Independent semantic versions

The repo SHALL version itself with Semantic Versioning, SHALL cut a new
version only when there are changes to ship, and SHALL tag each version
with its plain version number, without a `v` prefix.

#### Scenario: Nothing to ship in a month

- **WHEN** no user-visible change merged since the last version
- **THEN** no new version is cut that month, and its milestone moves to
  the next month

### Requirement: Unreleased section with a target

The top section of `CHANGELOG.md` SHALL be `## Unreleased`, and its first
line SHALL be `Target: <version> - <YYYY-MM-DD>`, giving the next version
and its planned cut date. The date alone SHALL decide which monthly
release the version ships in: the first one whose freeze starts after
that date. Below the `Target:` line, entries SHALL be grouped under Keep a
Changelog headings (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`,
`Security`), and an entry for work that is not merged yet SHALL end in
`(planned)`.

#### Scenario: Next version is planned

- **WHEN** the next version's planned content is known
- **THEN** `Unreleased` starts with its `Target:` line and lists that
  content, each merged entry referencing its PR in this repo (`#123`), and
  each entry for unmerged work ending in `(planned)`

#### Scenario: Planned work merges

- **WHEN** the PR doing work that has a `(planned)` entry merges
- **THEN** that PR updates the entry to match what changed, adds its PR
  number and removes the `(planned)` marker

### Requirement: Changelog kept current with each change

Any PR that changes what a user of coffeeAgntcy sees (an application
feature or behavior, its UI, its configuration, environment variables,
Compose files, Helm charts or images, the pattern library or event
schema, a documented task or contribution process) SHALL update
`Unreleased` in the same PR. Changes with no user-visible effect (an
internal CI fix, a test fix, a refactor) MAY be left out.

#### Scenario: PR fixes a deployment bug

- **WHEN** a PR fixes a bug in a Helm chart
- **THEN** the same PR adds a `Fixed` entry for it under `Unreleased`

### Requirement: Cutting a version

Cutting a version SHALL replace `Unreleased` with the detailed version
section produced by the `generate-release-notes` skill, headed
`## <version> (<YYYY-MM-DD>)` with a `Release: <Code name> (<Month
YYYY>)` line below it, SHALL move any entry still marked `(planned)` into
a fresh `## Unreleased` section above it with the next `Target:` line,
and, once merged, SHALL tag the resulting commit on `main` with the
version. The version section SHALL agree with the `Unreleased` entries it
replaces. The release PR SHALL be merged and the version tagged before
the freeze starts for the version to be part of that month's release.

#### Scenario: Version ready before freeze

- **WHEN** a version is merged and tagged before that month's freeze
- **THEN** it ships in that month's release, its section names that
  release on its `Release:` line, and it holds no `(planned)` entries

#### Scenario: Version not ready by freeze

- **WHEN** the planned version is not merged and tagged before the freeze
- **THEN** its content stays in `Unreleased`, the `Target:` date and the
  milestone's due date move, and it rolls into the next month's release
  under the same code name

#### Scenario: Patch after the cut

- **WHEN** a patch version is cut after its month's release already
  shipped
- **THEN** it ships in the next month's release and its `Release:` line
  names that release
