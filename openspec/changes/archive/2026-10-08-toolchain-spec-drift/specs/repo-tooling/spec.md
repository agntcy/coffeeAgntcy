# Spec Delta

## MODIFIED Requirements

### Requirement: A repo-local toolchain installs without touching the global system
`task setup` (equivalently `./scripts/setup.sh`) SHALL install `task`,
`actionlint`, `shellcheck`, `shfmt`, `bats`, `node`, `openspec`, and
`renovate` into this repo's own `.tools/` directory, and SHALL NOT modify
the invoking user's global `PATH`, shell profile, or home directory.
`source scripts/env.sh` SHALL put `.tools/bin`, `.tools/node/bin`, and
`.tools/bats/bin` on `PATH` for the invoking shell session only.

#### Scenario: Fresh clone with no toolchain installed
- **WHEN** `task setup` is run in a clone with no `.tools/` directory
- **THEN** every tool listed above is installed under `.tools/`, and no
  file outside this repo's working tree is modified
