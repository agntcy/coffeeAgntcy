# Description

Please provide a meaningful description of what this change will do, or is for.
Bonus points for including links to related issues, other PRs, or technical
references.

Note that by _not_ including a description, you are asking reviewers to do extra
work to understand the context of this change, which may lead to your PR taking
much longer to review, or result in it not being reviewed at all.

## Issue Link

Link the primary issue in the PR description using `#` (e.g. `Fixes #123`). This enables two‑way linking.

## Type of Change

- [ ] Bugfix
- [ ] New Feature
- [ ] Breaking Change
- [ ] Refactor
- [ ] Documentation
- [ ] Other (please describe)

## CI (automated checks)

- **Python (agent paths):** [smoke](.github/workflows/ci-smoke.yaml) runs on every push. **Integration** (`integration / corto|lungo|recruiter`) is **mandatory to merge** for all PRs. Same-repo PRs run integration on each push; **fork PRs** must receive an **Approve** from [`@agntcy/coffee-agntcy-reviewers`](https://github.com/orgs/agntcy/teams/coffee-agntcy-reviewers) before [fork integration](.github/workflows/integration-fork-approve.yaml) runs (once per commit; re-approve after new pushes).
- **Lungo frontend:** [FE CI](.github/workflows/fe-ci.yaml) (typecheck, ESLint, Prettier) when `lungo/frontend/**` changes.

## Checklist

- [ ] I have read the [contributing guidelines](/agntcy/coffeeAgntcy/blob/main/CONTRIBUTING.md)
- [ ] Existing issues have been referenced (where applicable)
- [ ] I have verified this change is not present in other open pull requests
- [ ] Functionality is documented
- [ ] All code style checks pass
- [ ] New code contribution is covered by automated tests
- [ ] All new and existing tests pass
