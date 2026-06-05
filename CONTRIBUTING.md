# How to Contribute

Thanks for your interest in contributing to `coffeeAgntcy`! Here are a few
general guidelines on contributing and reporting bugs that we ask you to review.
Following these guidelines helps to communicate that you respect the time of the
contributors managing and developing this open source project. In return, they
should reciprocate that respect in addressing your issue, assessing changes, and
helping you finalize your pull requests. In that spirit of mutual respect, we
endeavor to review incoming issues and pull requests within 10 days, and will
close any lingering issues or pull requests after 60 days of inactivity.

Please note that all of your interactions in the project are subject to our
[Code of Conduct](/CODE_OF_CONDUCT.md). This includes creation of issues or pull
requests, commenting on issues or pull requests, and extends to all interactions
in any real-time space e.g., Slack, Discord, etc.

## Reporting Issues

Before reporting a new issue, please ensure that the issue was not already
reported or fixed by searching through our [issues
list](https://github.com/agntcy/coffeeAgntcy/issues).

When creating a new issue, please be sure to include a **title and clear
description**, as much relevant information as possible, and, if possible, a
test case.

**If you discover a security bug, please do not report it through GitHub.
Instead, please see security procedures in [SECURITY.md](/SECURITY.md).**

## Sending Pull Requests

Before sending a new pull request, take a look at existing pull requests and
issues to see if the proposed change or fix has been discussed in the past, or
if the change was already implemented but not yet released.

We expect new pull requests to include tests for any affected behavior, and, as
we follow semantic versioning, we may reserve breaking changes until the next
major version release.

### CI: smoke and mandatory integration

For pull requests that change agent code (`corto`, `lungo`, `recruiter`):

1. **Smoke** tests run on every push (no LLM secrets).
2. **Integration** tests are **required to merge** for everyone. They use repo LLM/Azure secrets and must pass on the PR’s latest commit for each affected project.

**Same-repo branches:** integration runs automatically when you push.

**Fork PRs:** integration runs only after a member of `@agntcy/coffee-agntcy-reviewers` submits an **Approve** review on GitHub. Until then, required `integration / *` checks stay pending and merge is blocked. After you push new commits, a new **Approve** is needed before integration runs again (once per commit SHA).

See [`.github/workflows/README.md`](.github/workflows/README.md) for workflow details and branch protection setup.

Run smoke tests locally before opening a PR:

```bash
cd coffeeAGNTCY/coffee_agents/lungo && uv run pytest tests/unit -m "not e2e" -q
cd coffeeAGNTCY/coffee_agents/corto && uv run pytest tests/unit -q
cd coffeeAGNTCY/coffee_agents/recruiter && uv run pytest tests/ --collect-only -q
```

## Other Ways to Contribute

We welcome anyone that wants to contribute to `coffeeAgntcy` to triage and
reply to open issues to help troubleshoot and fix existing bugs. Here is what
you can do:

- Help ensure that existing issues follows the recommendations from the
  _[Reporting Issues](#reporting-issues)_ section, providing feedback to the
  issue's author on what might be missing.
- Review existing pull requests, and testing patches against real existing
  applications that use `coffeeAgntcy`.
- Write a test, or add a missing test case to an existing test.

Thanks again for your interest on contributing to `coffeeAgntcy`!

:heart:
