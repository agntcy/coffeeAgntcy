# Tasks

Branch `879-check-sweep`, tracked by issue #879. Run everything from the repo
root after `source scripts/env.sh`. Tests come first in each group (see the
`bash-script-testing` rule).

## 1. Pin and asset definition

- [x] 1.1 Write the failing tests in `scripts/tools/tests/update_checksums.bats`:
  `asset_url dir-mcp <os> <arch>` returns
  `https://github.com/agntcy/dir-mcp/releases/download/v1.3.8-mcp.1/mcp-server-<os>-<arch>`
  for darwin and linux on amd64 and arm64, and `update_checksums.bash` writes one
  line per platform for it (adjust any hardcoded line count or tool list there).
  Verify: `bats scripts/tools/tests/update_checksums.bats` fails on the new cases.
- [x] 1.2 Add `DIR_MCP_VERSION="1.3.8-mcp.1"` to `scripts/lib/versions.sh` in
  alphabetical position (after `BATS_VERSION`) with
  `# renovate: datasource=github-releases depName=agntcy/dir-mcp extractVersion=^v(?<version>.*)$`,
  add `dir-mcp` to `ASSET_TOOLS` (alphabetical: after `bats`) and the `dir-mcp)`
  case to `asset_url` in `scripts/lib/assets.sh`. Update the "bump" comment in
  `versions.sh` if it lists tools. Verify: the 1.1 tests pass.
- [x] 1.3 Check `scripts/tools/tests/print_versions.bats` still passes; extend its
  expected tool list if it hardcodes one. Verify: `bats scripts/tools/tests/`.
- [x] 1.4 (superseded in part by 1.7-1.8: the verifier is the hash-pinned venv's `sigstore`, not `uv tool run`) Write the failing tests in `scripts/tools/tests/update_checksums.bats`
  with `uv` mocked on `PATH` (only `uv` is installed, not `uvx`) (see how `curl` is mocked there): (a) a passing
  mock makes the script write the four `dir-mcp` lines and the mock received
  `--from sigstore==<SIGSTORE_VERSION>`, `verify identity`, the bundle path,
  `--cert-identity https://github.com/agntcy/dir-mcp/.github/workflows/release.yml@refs/tags/v<DIR_MCP_VERSION>`
  and `--cert-oidc-issuer https://token.actions.githubusercontent.com`; (b) a mock
  that exits non-zero makes the script exit non-zero naming the asset and write no
  `dir-mcp` line (the file keeps its previous content); (c) tools other than
  `dir-mcp` never call `uvx`. Verify: the new cases fail.
- [x] 1.5 Add `SIGSTORE_VERSION="4.5.1"` to `scripts/lib/versions.sh` in alphabetical
  position (after `SHFMT_VERSION`) with `# renovate: datasource=pypi depName=sigstore`
  (4.5.1 is the newest release at least two weeks old; 4.6.0 is too new), and implement the verification in
  `scripts/tools/update_checksums.bash`: for `dir-mcp` only, fetch the
  `<asset-url>.sigstore.json` bundle, run the sigstore verification from D5 (superseded in part by 1.7-1.8: the command runs the hash-pinned venv's `sigstore`) on the
  downloaded asset, fail closed, and write the output file only when everything
  verified. Verify: the 1.4 tests pass and `bats scripts/tools/tests/`.
- [x] 1.6 Run the real `task tools:checksums` and review the diff: exactly four new
  `mcp-server-*` lines, nothing else changed, and the log shows four
  verifications. Cross-check one hash against the darwin-arm64 asset
  (`84ec804f56ca51da8faa01f6e64bb6c6d91e914458e4587ff475a31e4195bf18` was
  observed for `mcp-server-darwin-arm64` at `v1.3.8-mcp.1`). Verify:
  `git diff --stat scripts/lib/checksums.txt` shows 4 insertions.

- [x] 1.7 Hash-pin the verifier (design D6). Tests first in a new
  `scripts/tools/tests/update_sigstore_lock.bats`: the generator
  `scripts/tools/update_sigstore_lock.bash` (mirror `update_npm_lock.bash` and its
  test, including how the repo exposes it as a task) writes
  `scripts/lib/sigstore/requirements.txt` by running, with `uv` mocked,
  `uv pip compile <input containing sigstore==$SIGSTORE_VERSION> --universal
  --generate-hashes --python-version 3.10 --exclude-newer "14 days" --no-config -o <file>` (use the lowest Python the
  sigstore release supports so the universal file works on every machine); add
  `task tools:sigstore-lock` to `Taskfile.yaml` and the `manage-repo-tooling`
  skill's bump checklist. Then run it for real and commit-ready review the file:
  it must contain `sigstore==4.5.1`, every package with at least one
  `--hash=sha256:`, and no unhashed line. Verify: the new bats pass and
  `grep -c "sigstore==4.5.1" scripts/lib/sigstore/requirements.txt` prints 1.
- [x] 1.8 Switch `update_checksums.bash` from `uv tool run` to the hash-enforced
  install (design D6): create a throwaway venv under `TMP_DIR` with `uv venv`,
  `uv pip install --python <venv>/bin/python --require-hashes --no-deps -r
  scripts/lib/sigstore/requirements.txt`, run `<venv>/bin/sigstore verify
  identity ...` with the same flags as before, and exit non-zero before any
  verification when the requirements file's `sigstore==` pin differs from
  `SIGSTORE_VERSION` (message names `task tools:sigstore-lock`). Update the
  mocks in `update_checksums.bats` so `uv venv`, `uv pip install` and the venv's
  `sigstore` are mocked, and add cases: install failure (hash mismatch exit) writes
  no `dir-mcp` line; pin mismatch fails with the task name; the install uses
  `--require-hashes`. Verify: `bats scripts/tools/tests/` passes in full, then a
  corrupted copy of the real requirements file makes a real
  `uv pip install --require-hashes` fail (record the output in the report).
- [x] 1.9 Re-run the real `task tools:checksums` and confirm the four `dir-mcp`
  lines are unchanged and four `OK:` verifications appear (now via the
  hash-pinned venv). Verify: `git diff --stat scripts/lib/checksums.txt` still shows
  exactly 4 insertions in total.

## 2. Install step in setup.sh

- [x] 2.1 Write the failing tests in `scripts/tests/setup.bats`, following the
  shfmt cases: (a) a fresh fixture run installs an executable
  `.tools/bin/dir-mcp` whose bytes equal the served asset and writes
  `.tools/stamps/dir-mcp` containing `1.3.8-mcp.1`; (b) a second run prints
  `dir-mcp: already installed` and fetches nothing; (c) a stamp naming another
  version, and (d) a missing stamp, each print `dir-mcp: installing 1.3.8-mcp.1`
  and rewrite the stamp; (e) a served asset that does not match its pinned
  checksum is rejected and leaves no `.tools/bin/dir-mcp`. Extend
  `build_fixture_assets`, `write_fixture_checksums`, `install_curl_mock` and
  `seed_all_installed_except` so every other test still seeds dir-mcp.
  Verify: `bats scripts/tests/setup.bats` fails exactly on the new cases.
- [x] 2.2 Implement the install block in `scripts/setup.sh` next to the shfmt
  block: skip when `[ -x "$BIN_DIR/dir-mcp" ]` and the stamp equals
  `$DIR_MCP_VERSION`; otherwise `FETCH_VERIFIED "$(asset_url dir-mcp "$OS" "$ARCH_GNU")"`
  into a temp file, `install` it as `$BIN_DIR/dir-mcp`, write the stamp, print
  `dir-mcp: installed`. Add a comment that the binary has no `--version`, so the
  stamp stands in for `version_matches`. Verify: `bats scripts/tests/setup.bats`
  passes in full.
- [x] 2.3 Run `task shell:lint` (shellcheck and shfmt) and `task tests:coverage`.
  Verify: both exit 0.

## 3. Documentation

- [x] 3.1 Update every document that lists the toolchain: the `setup` task
  description in `Taskfile.yaml`, the `setup-repo-tooling` and
  `manage-repo-tooling` skills, `.agents/rules/meta/pinned-tool-versions.md` if it
  enumerates tools, and the `repo-tooling` spec via the change delta
  (`specs/repo-tooling/spec.md`). Verify: `task links:check` and
  `task dashes:check` pass and `grep -rn "dir-mcp" Taskfile.yaml` shows the new
  entries (`CONTRIBUTING.md` lists no tools beyond shellcheck, shfmt and
  actionlint, so it needs no edit).
- [x] 3.2 In `coffeeAGNTCY/coffee_agents/recruiter/README.md`, say that
  `task setup` followed by `source scripts/env.sh` provides `dir-mcp` for local
  (non-Docker) MCP mode and for the integration tests, and keep the manual
  release-page install as the fallback. Verify: `task links:check`.

## 4. Renovate and end-to-end verification

- [x] 4.1 Read `renovate.json` and the `sync-renovate` skill: confirm how the
  `# renovate:` comment in `versions.sh` is picked up and that a newer
  `v1.3.8` tag cannot silently move the pin away from the compose image's
  `1.3.8-mcp.1`; if it can, constrain it (allowedVersions or a shared group with
  the compose image). Verify: `task renovate:sync` leaves no diff, and the
  decision is recorded in design.md Risks.
- [x] 4.2 Run the real setup on this machine: `task setup`, then
  `source scripts/env.sh && command -v dir-mcp`, and run
  `.tools/bin/dir-mcp </dev/null` to confirm it starts and answers on stdio.
  Re-run `task setup` and confirm `dir-mcp: already installed`. Verify: the path
  printed is `.tools/bin/dir-mcp`.
- [x] 4.3 Re-run the recruiter tests that failed for want of the binary:
  `cd coffeeAGNTCY/coffee_agents/recruiter && uv run pytest -v tests/integration/llm`
  (Docker running, no other clone's stack up), and report which of the 3 failures
  and 4 errors remain. Verify: none of them mentions
  `dir-mcp binary not found`.
- [x] 4.4 Run `task check:all` and an independent subagent review of the diff
  (see the sweep's review rounds). Verify: all checks pass except the known
  `tests:bash` environment failures, which are reported as such.
