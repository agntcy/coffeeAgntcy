# Tasks

## 1. uv image

- [x] 1.1 Add `scripts/tools/update_uv_image.bash` and `task tools:sync-uv` (the task wraps that script only). The script reads `UV_VERSION`, fetches the `astral/uv:<UV_VERSION>-python3.13-trixie-slim` manifest-list digest when `scripts/lib/uv-image.txt` is missing or names a different version, and rewrites that record and the `@sha256:` in `docker/Dockerfile.python-agent`. It exits 0 without network when the record already matches. Verify with a bats test that a fixture tree is rewritten to a supplied digest and that a second run leaves the fixture unchanged.
- [x] 1.2 Fetch the live manifest-list digest for the current `UV_VERSION` and confirm the tag exists (`docker buildx imagetools inspect astral/uv:<UV_VERSION>-python3.13-trixie-slim`). If the tag does not exist, stop and report that instead of inventing a digest. Commit `scripts/lib/uv-image.txt` with the digest that command prints. Change `docker/Dockerfile.python-agent` to `ARG UV_VERSION` with no default and `FROM astral/uv:${UV_VERSION}-python3.13-trixie-slim@<that digest>`. Leave the dir-ctl and dir-mcp `FROM` lines as they are. Verify the digest field equals the `@sha256:` in the Dockerfile, and that `python3.13-trixie-slim` is still a literal.

## 2. Callers pass UV_VERSION

- [x] 2.1 Export `UV_VERSION` from `scripts/env.sh` the same way `NODE_VERSION` is exported. Export no other pin. Verify `source scripts/env.sh` sets both `NODE_VERSION` and `UV_VERSION` to the values in `versions.sh`, and that `HELM_VERSION` is not exported.
- [x] 2.2 Pass `UV_VERSION: ${UV_VERSION:?source scripts/env.sh so UV_VERSION is set}` from every compose service that builds `docker/Dockerfile.python-agent` (corto, lungo, and recruiter). In `.github/workflows/docker-build-reusable.yaml`, source `versions.sh` and pass `UV_VERSION` only when the dockerfile is `docker/Dockerfile.python-agent`. Do not pass it to the UI image. Update the `docker build` examples in `docker/README.corto.md`, `docker/README.lungo.md`, and `docker/README.recruiter.md` to source `scripts/env.sh` and pass `--build-arg UV_VERSION`. Verify `docker compose config` for one corto Python service and one lungo Python service fails with the guard message when `UV_VERSION` is unset and succeeds after `source scripts/env.sh`.

## 3. Helm CI

- [x] 3.1 Change `.github/workflows/helm-package-reusable.yaml` so a step sources `scripts/lib/versions.sh` and `azure/setup-helm` receives `${HELM_VERSION#v}`. Remove the `version: "4.3.0"` literal. Verify `task workflows:lint` passes, the file no longer contains a quoted Helm version, and the buildx `# v4.3.0` comment is unchanged.

## 4. Check

- [x] 4.1 Extend `scripts/checks/check_versions.bash` with one function per remaining pin: uv image tag and digest, Helm workflow, npm lockfile direct versions, OpenSpec skill `generatedBy` stamps, and the single-install tools (setup and assets still expand the variable, and no workflow or Dockerfile installs actionlint, bats, shellcheck, shfmt, or task at a numeric version). Reword the `v` prefix sentence in `.agents/rules/meta/pinned-tool-versions.md` so it no longer quotes the live shfmt and task versions. Verify a bats fixture passes on a tree that reads the variables, and fails on each of: a numeric `astral/uv:` tag, a digest that disagrees with `uv-image.txt`, a missing compose `UV_VERSION` arg, a numeric Helm `version:`, a lockfile openspec or renovate version other than the pin, a `generatedBy` stamp other than `OPENSPEC_VERSION`, and a workflow that installs shellcheck at a number. Verify a `# v4.3.0` comment on an unrelated action does not fail the Helm check.
- [x] 4.2 In `openspec/changes/sync-node-version/specs/repo-tooling/spec.md`, remove the sentences that say `versions:check` has no function for any other pin and still exits zero when another pin has drifted. Keep the Node requirements. Verify `openspec validate --strict --type change sync-node-version` and `openspec validate --strict --type change sync-tool-versions` both pass.

## 5. Renovate and the rule

- [x] 5.1 Add `scripts/tools/update_uv_image.bash` to the toolchain `postUpgradeTasks` in `renovate.json` (command and file filters for `uv-image.txt` and `docker/Dockerfile.python-agent`) and to `RENOVATE_ALLOWED_COMMANDS` in `.github/workflows/renovate.yaml`. Disable the dockerfile manager for the `astral/uv` image in `docker/Dockerfile.python-agent` only, so the dir-ctl and dir-mcp lines stay managed. If a package rule cannot target that one image, record the fallback in `.agents/rules/quality/version-sync.md`: the generator rewrites the uv `FROM` line back to the `ARG` form in the same post-upgrade run. Extend that rule so it covers every `versions.sh` pin, not only Node. Verify `task workflows:lint` passes and the allowed-command pattern matches the new script path.

## 6. Integration

- [x] 6.1 Build one Python agent image with `UV_VERSION` set (`docker build` of `docker/Dockerfile.python-agent` for one corto service is enough) and confirm it completes. Then run `task dashes:check`, `task shell:lint`, and `task check:all`. Verify all four exit 0, and that `task versions:check` is one of the PASS lines.
