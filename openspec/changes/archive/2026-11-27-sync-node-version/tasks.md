# Tasks

## 1. Generator

- [x] 1.1 Add `scripts/tools/update_node_version.bash` and `task tools:sync-node` (the task wraps that script only). The script reads `NODE_VERSION`, fetches the `node:<NODE_VERSION>-alpine` manifest-list digest when `scripts/lib/node-image.txt` is missing or names a different version, and rewrites that record, the `@sha256:` in `docker/Dockerfile.ui`, both frontend `engines.node` floors (package.json and the root engines object in each package-lock.json), and the Node install sentence in `TUTORIAL.md`, `coffeeAGNTCY/coffee_agents/corto/README.md`, `coffeeAGNTCY/coffee_agents/lungo/README.md`, and both frontend READMEs. It exits 0 without network when the record already matches. Verify with a bats test that a fixture tree is rewritten to a supplied digest and that a second run leaves the fixture unchanged.
- [x] 1.2 Fetch the live manifest-list digest for the current `NODE_VERSION` and confirm it equals `docker buildx imagetools inspect node:26.13.1-alpine` (or the tag `NODE_VERSION` names if the pin has moved). Commit `scripts/lib/node-image.txt` with that digest. Verify the digest field equals the `@sha256:` already in `docker/Dockerfile.ui`.

## 2. Installs read the variable

- [x] 2.1 Export `NODE_VERSION` from `scripts/env.sh` after sourcing `scripts/lib/versions.sh`. Do not export the other pins. Verify `source scripts/env.sh && test -n "$NODE_VERSION"` prints a match against the value in `versions.sh`, and that `UV_VERSION` is not exported.
- [x] 2.2 Change `docker/Dockerfile.ui` to `ARG NODE_VERSION` with no default and `FROM node:${NODE_VERSION}-alpine@<digest from node-image.txt>`. Pass `NODE_VERSION: ${NODE_VERSION:?source scripts/env.sh so NODE_VERSION is set}` from the UI services in both `docker-compose.yaml` files. In `.github/workflows/docker-build-reusable.yaml`, source `versions.sh` and append `NODE_VERSION` to the build-args only when the dockerfile is `docker/Dockerfile.ui`. Verify `task pins:check` passes, and that `docker compose config` for the lungo UI service fails with the guard message when `NODE_VERSION` is unset and succeeds after `source scripts/env.sh`.
- [x] 2.3 Change `.github/workflows/fe-ci.yaml` so a step sources `scripts/lib/versions.sh` and `actions/setup-node` receives that step output. Remove the `node-version` literal. Verify `task workflows:lint` passes and the file no longer contains a quoted Node version.
- [x] 2.4 Run `task tools:sync-node` so the five docs and both engine floors name the current `NODE_VERSION`, and update the UI `docker build` examples in `docker/README.corto.md` and `docker/README.lungo.md` to source `scripts/env.sh` and pass `--build-arg NODE_VERSION`. Verify each of those files contains the current pin and the docker examples contain `NODE_VERSION`.

## 3. Check

- [x] 3.1 Add `scripts/checks/check_versions.bash` with a single `check_node` function, as design decision 3 describes, and `task versions:check` wrapping only that script. Verify a bats fixture (same copy-into-a-fake-repo shape as `check_pinned_references.bats`) passes on a tree that reads the variable, and fails on each of: a numeric `node-version`, a numeric `node:` tag, a digest that disagrees with `node-image.txt`, a missing compose build-arg, an `engines.node` floor other than `>=` plus the pin, and a doc sentence with a different version. Verify the fixture still passes when a non-Node pin is hardcoded differently from `versions.sh`.
- [x] 3.2 Add `versions:check` to `scripts/checks/check_all.bash`. Update `scripts/checks/tests/check_all.bats` so the "all twelve" count and the PASS lines include `versions:check`. Verify `task tests:bash` passes for `check_all.bats` and `check_versions.bats`.

## 4. Pipeline and Renovate

- [x] 4.1 Add `.agents/rules/quality/version-sync.md` and `.agents/skills/quality-checks/checking-version-sync/SKILL.md`. Index both in `AGENTS.md` (alphabetized in their sections). Add a `versions:check` row to `.agents/rules/always-apply/pre-finalize-checks.md` and change "all twelve" to "all thirteen". Update the check list in `.github/workflows/README.md` and `CONTRIBUTING.md` if it names the set. Extend `pinned-tool-versions` and the `manage-repo-tooling` skill so a `NODE_VERSION` bump runs `task tools:sync-node` then `task versions:check`. Note the `scripts/env.sh` export in `setup-repo-tooling`. Verify `task pipeline:check-exceptions` passes and `task links:check` passes.
- [x] 4.2 Add `scripts/tools/update_node_version.bash` to the toolchain `postUpgradeTasks` in `renovate.json` (command and file filters for `node-image.txt`, `Dockerfile.ui`, the two `package.json` files, the two lockfiles, and the five docs) and to `RENOVATE_ALLOWED_COMMANDS` in `.github/workflows/renovate.yaml`. If the current Renovate dockerfile manager would rewrite `FROM node:${NODE_VERSION}...` into a numeric tag, add a `matchFileNames` rule so `docker/Dockerfile.ui` stays with the ARG form, and record that in the version-sync rule. Verify `task workflows:lint` passes and the allowed-command pattern matches the script path.

## 5. Integration

- [x] 5.1 Run `task dashes:check`, `task shell:lint`, and `task check:all`. Verify all three exit 0, and that `task versions:check` is one of the PASS lines.
