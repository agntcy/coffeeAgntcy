# Tasks

## 1. Release policy and changelog

- [x] 1.1 Add a "Releases" section to `CONTRIBUTING.md` (cadence, freeze,
      named releases, versioning, keeping `Unreleased` current, cutting
      a version pointing at `docs/RELEASE-OPS.md`), and link it from the
      PR flow; verify every anchor and link resolves (`task links:check`)
- [x] 1.2 Rewrite `CHANGELOG.md`'s `## Unreleased` with an intro line, a
      `Target: 0.5.0 - 2026-10-27` line, entries for the user-visible PRs
      merged since `0.4.0`, and `(planned)` entries for the open Nexus
      milestone work; verify earlier version sections are unchanged
      (`git diff` touches only the top of the file)
- [x] 1.3 Add `.agents/rules/always-apply/keep-changelog-current.md` and
      list it in `AGENTS.md`, `keep-docs-consistent.md`,
      `repo-operation-pipeline.md`'s "Known exceptions" and
      `check_pipeline_exceptions.bash`'s `RULE_ONLY_EXCEPTIONS`; verify
      with `task pipeline:check-exceptions` and `task tests:bash`

## 2. Runbook and release-notes tooling

- [x] 2.1 Align `docs/RELEASE-OPS.md` with the policy: freeze timing,
      milestone due dates, replacing `Unreleased` with the generated
      section and its `Release:` line, the fresh `Unreleased`, and the
      release title for every version; verify by reading it end to end
      against the spec's "Cutting a version" scenarios
- [x] 2.2 Update `.agents/prompts/release-notes/PROMPT.md`, `example.md`
      and the `generate-release-notes` skill so `Unreleased` is the
      authoritative input, the title carries the `Release:` line, and the
      output replaces `Unreleased`; verify the skill workflow, prompt and
      runbook describe the same steps

## 3. Contributor-facing surfaces

- [x] 3.1 Add a "Changelog" section to `.github/pull_request_template.md`;
      verify it renders as a comment prompt like the other sections
- [x] 3.2 Turn the README milestones table into a releases table (code
      name, month, version, focus, date) covering Heartbeat to Nexus;
      verify versions and dates against `git tag` and `gh release list`

## 4. Integration checks

- [x] 4.1 Run `task check:all` and `openspec validate monthly-named-releases
      --strict`; both pass
- [x] 4.2 Grep the changed files for anything outside this repo's own
      context (other repositories, organizations, internal planning
      terms); none found
