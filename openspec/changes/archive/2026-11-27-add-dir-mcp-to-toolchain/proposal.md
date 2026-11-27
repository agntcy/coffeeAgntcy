# Proposal

## Why

The recruiter's discovery toolset starts the `dir-mcp` binary found on `PATH`
(`registry_search_agent.py` uses `shutil.which("dir-mcp")` and raises when it is
missing), so its LLM and integration tests fail on any machine where nobody
installed `dir-mcp` by hand. The repo already bootstraps every other tool it
needs through `task setup`; `dir-mcp` is the one tool that still requires a
manual download from a release page.

Tracked by issue #879.

## What Changes

- Pin `dir-mcp` in `scripts/lib/versions.sh` at `1.3.8-mcp.1`, the release that
  matches the `ghcr.io/agntcy/dir-mcp:1.3.8-mcp.1` image the compose files
  already run, so Docker mode and local mode stay on one version.
- Add `dir-mcp` to the directly downloaded tools in `scripts/lib/assets.sh`
  (release asset `mcp-server-<os>-<arch>`, a raw binary for the four supported
  platforms) and pin its SHA-256 for each platform in
  `scripts/lib/checksums.txt`.
- `scripts/setup.sh` installs it as `.tools/bin/dir-mcp` through the existing
  verified fetch, so `source scripts/env.sh` puts it on `PATH`.
- Detect version drift without running the binary: `dir-mcp` is a silent stdio
  MCP server with no `--version` output, so `setup.sh` records the installed
  version in a stamp file next to the toolchain and compares that with the pin.
- Verify the release's sigstore bundles when the checksums are generated:
  `scripts/tools/update_checksums.bash` checks each `dir-mcp` asset against its
  `.sigstore.json` bundle (signer: the `dir-mcp` release workflow at the pinned
  tag, issuer: GitHub Actions) before recording its SHA-256, using `sigstore`
  installed through the already pinned `uv`, with `sigstore` pinned in
  `versions.sh` and the package and all its transitive dependencies pinned by
  SHA-256 in a committed `scripts/lib/sigstore/requirements.txt`
  (`task tools:sigstore-lock` regenerates it). Setup keeps checking only the
  SHA-256, offline.
- Document the new tool where the toolchain is described.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `repo-tooling`: the repo-local toolchain gains `dir-mcp`, and the drift
  requirement now covers a tool that cannot report its own version.

## Impact

- Code: `scripts/lib/versions.sh`, `scripts/lib/assets.sh`,
  `scripts/lib/checksums.txt`, `scripts/setup.sh`,
  `scripts/tools/update_checksums.bash`, `scripts/tools/print_versions.bash`
  (hyphenated tool names), the new `scripts/tools/update_sigstore_lock.bash` and
  the generated `scripts/lib/sigstore/requirements.txt`, the `tools:sigstore-lock`
  task in `Taskfile.yaml`, `.gitignore` (un-ignores that lock file).
- CI and Renovate: `renovate.json` (post-upgrade commands and the `DIR_MCP_VERSION`
  versioning), `.github/workflows/renovate.yaml` (the allowed-commands list gains
  exactly the lock generator).
- Tests: `scripts/tests/setup.bats`, `scripts/tools/tests/update_checksums.bats`,
  `scripts/tools/tests/print_versions.bats` and the new
  `scripts/tools/tests/update_sigstore_lock.bats`.
- Docs: recruiter README, the `repo-tooling` spec, the `setup-repo-tooling`,
  `manage-repo-tooling` and `sync-renovate` skills, the `pinned-tool-versions`
  rule, the `setup` task description in `Taskfile.yaml`.
- Dependencies: one more pinned download from `github.com/agntcy/dir-mcp`, and
  `sigstore` (hash-pinned with its transitive packages) used only when checksums
  are generated; no change to any runtime dependency of the agents.
