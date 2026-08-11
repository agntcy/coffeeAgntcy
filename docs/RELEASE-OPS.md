# Release Operations

This document describes the end-to-end steps for cutting a **version release** of [coffeeAgntcy](https://github.com/agntcy/coffeeAgntcy/) on GitHub.

It is intentionally **not** specific to any single release version. Anything that would not always be true is shown as an **example** and uses placeholders such as `<version>`, `<tag>`, and `<milestone>`. Replace placeholders with the real values for the release you are cutting.

Placeholders used throughout:

| Placeholder    | Meaning                                                           | Example              |
| -------------- | ----------------------------------------------------------------- | -------------------- |
| `<version>`    | The semver version being released                                 | `0.3.0`              |
| `<tag>`        | The git tag for the release (this repo tags **without** a `v` prefix) | `0.3.0`          |
| `<milestone>`  | The GitHub Milestone associated with the release                  | `Synapsis`           |
| `<email>`      | Your sign-off email                                               | `you@cisco.com`      |

> Convention note: existing release tags in this repo are plain semver (`0.2.0`, `0.2.1`, `0.3.0`), i.e. **no** `v` prefix. `*-dev*` tags are throwaway/dev tags and are **not** release tags. Match whatever the existing release tags use.

---

## Step 0 - Verify the Helm chart version-bump rule was followed

Before anything else, confirm everyone honored the rule that **any change to a Helm chart's contents must be accompanied by a version bump in that chart's `Chart.yaml`**. If the latest chart contents are not covered by a chart-version bump, the release tag would ship un-versioned chart changes.

**1. Check `main` against the last real/release tag** (ignore `*-dev*` tags):

```sh
# Latest release tag (excludes "-dev" tags); adjust the grep to your tag scheme.
git fetch --tags
LAST_RELEASE_TAG=$(git tag --list --sort=-creatordate | grep -Ev '\-dev' | head -n1)
echo "Last release tag: ${LAST_RELEASE_TAG}"

# What changed under the Helm chart trees since that tag?
git diff --name-only "${LAST_RELEASE_TAG}"..main -- coffeeAGNTCY/coffee_agents/lungo/deployment/helm coffeeAGNTCY/coffee_agents/corto/deployment/helm
```

**2. Confirm each changed chart bumped its `Chart.yaml`.** The Helm chart directories live under two umbrellas:

- `coffeeAGNTCY/coffee_agents/lungo/deployment/helm/<chart>/`
- `coffeeAGNTCY/coffee_agents/corto/deployment/helm/<chart>/`

For **each** chart directory that changed, find the last PR that merged a change to the chart's contents and confirm that PR (or a later one) also bumped the `version:` field in that chart's `Chart.yaml`.

```sh
# For a given chart dir, review recent history of its contents vs. its Chart.yaml.
CHART_DIR="coffeeAGNTCY/coffee_agents/lungo/deployment/helm/ui"   # example chart

# The list of commits resulting from the next two commands should, ideally, be identical.
git log --oneline "${LAST_RELEASE_TAG}"..main -- "${CHART_DIR}"
git log --oneline "${LAST_RELEASE_TAG}"..main -- "${CHART_DIR}/Chart.yaml"

# Ultimately, we only really need for the most recent commit that updated the contents of a chart to also have updated its Chart.yaml.
# Compare the newest commit touching the chart body against the newest commit that bumped its version line.
# If the body change is newer than (not an ancestor of) the version bump, the chart needs a bump.
git log -1 --oneline "${LAST_RELEASE_TAG}"..main -- "${CHART_DIR}" ":(exclude)${CHART_DIR}/Chart.yaml"   # newest body change
git log -1 --oneline "${LAST_RELEASE_TAG}"..main -G'^\s*version:' -- "${CHART_DIR}/Chart.yaml"           # newest version bump

# The following snippet automates that verdict for the chart: capture both commits, then test ancestry.
BODY=$(git log -1 --format=%H "${LAST_RELEASE_TAG}"..main -- "${CHART_DIR}" ":(exclude)${CHART_DIR}/Chart.yaml")
BUMP=$(git log -1 --format=%H "${LAST_RELEASE_TAG}"..main -G'^\s*version:' -- "${CHART_DIR}/Chart.yaml")
{ [ -z "${BODY}" ] || { [ -n "${BUMP}" ] && git merge-base --is-ancestor "${BODY}" "${BUMP}"; }; } \
  && echo "OK: ${CHART_DIR}" || echo "NEEDS BUMP: ${CHART_DIR}"
```

A `Chart.yaml` looks like this (the `version:` line is the chart version to bump):

```yaml
apiVersion: v1
appVersion: "0.0.9"
description: A Helm chart for Lungo UI
name: lungo-ui
version: 0.1.6      # <-- must increase when the chart's contents change
```

**3. If a chart's contents changed without a `version` bump, fix it now:**

- Open a small **version-bump PR** that increments the chart's `version:` in `Chart.yaml` (and any umbrella `Chart.yaml` dependency pin that references it).
- Get it **merged into `main`** so that the latest chart contents are captured by a chart version before the release tag is created.

---

## Step 1 - Finish the GitHub Milestone

Do this when all subtickets for the release are done.

1. Navigate to the milestones list: [https://github.com/agntcy/coffeeAgntcy/milestones](https://github.com/agntcy/coffeeAgntcy/milestones)

   - From the repository page, this is **Issues → Milestones** in the left sidebar.

2. Open the release's milestone `<milestone>` (if one exists).

3. Verify **all issues/PRs in the milestone are complete**. If any are not:

   - **Complete** them, or
   - **Move** the unfinished ones to the next release's milestone.

4. Click **Close milestone**.

5. Rename the milestone to its **canonical name only** and set the **release date** to the current date.
   - Usually the rename means removing the `(current release)` trailer
      - Example: rename `Synapsis (current release)` → `Synapsis`.

6. Click **Save**.

7. Go back to the milestones list and click **New milestone** to create the **next** current milestone by canonical name and current designation. **Include the `(current release)` trailer.**

   - Example: create `Cerebro (current release)`.

8. Move the **next release** milestone's issues over into the new `(current release)` milestone. If the issue list spans **multiple pages**, repeat this move for **each page**.

---

## Step 2 - Generate release notes, update README + CHANGELOG, and PR them

The [`generate-release-notes`](../.agents/skills/generate-release-notes/SKILL.md) skill does the heavy lifting.

**1. Update the version inputs** in [`.agents/prompts/release-notes/params.yaml`](../.agents/prompts/release-notes/params.yaml) so `previous_version` and `current_version` describe this release:

```yaml
# Edit before each release-notes run.
previous_version: "<previous_version>"
current_version: "<version>"
repo_url: "https://github.com/agntcy/coffeeAgntcy"
github_repo: "agntcy/coffeeAgntcy"
```

For example, when going from the `0.2.1` release to the `0.3.0` release, roll the values forward:

```yaml
# Before (used for the previous run):
previous_version: "0.2.0"
current_version: "0.2.1"

# After (this release):
previous_version: "0.2.1"
current_version: "0.3.0"
```

**2. Run the `generate-release-notes` skill.** It reads `params.yaml`, collects merged PRs since `previous_version`, reads the dependency lockfiles, and produces the release note text.

**3. Proof-read** the CHANGELOG entry for accuracy (versions, PR links, migration steps).

**4. Apply the generated output to the repo:**

- Update the **`### Built With`** section of [`README.md`](../README.md) with the versions from the generated notes.
- Add a new [`CHANGELOG.md`](../CHANGELOG.md) entry at the top (below the `# Changelog` heading), and add a `---` horizontal-rule separator at the **end** of the entry.

**5. Put these updates into a PR** and get it **merged** into `main`.

> Keep the CHANGELOG entry text handy - you will reuse it verbatim as the tag annotation in Step 3 and the GitHub Release body in Step 6.

---

## Step 3 - Create the annotated, signed tag on `main`

Make sure your local `main` is up to date with the merged Step 2 PR, then create **one** tag. Use the **milestone name** as the tag if this is a milestone release; otherwise use `<version>`.

```sh
git checkout main
git pull --ff-only

git tag -a --cleanup whitespace --sign --trailer "Signed-off-by: <Your Name> <<email>>" <tag>
```

For the tag **annotation** (equivalent to a commit message), paste the **release note** generated in Step 2.

> Important: remove the leading `##` markdown heading prefix from the **first line** of the annotation. For example, change the annotation's first line:
>
> ```text
> ## 0.3.0 (2026-08-10)
> ```
>
> to:
>
> ```text
> 0.3.0 (2026-08-10)
> ```

---

## Step 4 - Push the tag

One command:

```sh
git push origin <tag>   # example tag: 0.3.0
```

---

## Step 5 - Wait for CI

Watch the GitHub Actions run triggered by the pushed tag until everything finishes: [https://github.com/agntcy/coffeeAgntcy/actions](https://github.com/agntcy/coffeeAgntcy/actions)

- On **transient** failures (flaky network, registry hiccups, timeouts), **re-run** the failed jobs via **Re-run jobs → Re-run failed jobs** on the workflow run page.
- Only proceed once the release workflows are green.

---

## Step 6 - Create the public GitHub Release from the tag

Publish a release using the **same release note** from Step 2.

1. Go to the tags page: [https://github.com/agntcy/coffeeAgntcy/tags](https://github.com/agntcy/coffeeAgntcy/tags)

2. Click on the **newly pushed tag** `<tag>`.

3. On the resulting tag page, click the **"Create release from tag"** button in the **top-right**.

4. Set the release title and paste the release note as the release body, then click **Publish release**.

   - The **release tile** (do NOT confuse it with the `##` heading in the release note body!) should follow this format: `<tag> - <Milestone> (<YYYY-MM-DD>)`
   - For example: `0.3.0 - Synapsis (2026-08-10)`

---

## Step 7 - Update private deployments

Update container images and Helm charts versions in your private deployment environments to use the ones referenced by the tag.

   - Container images will likely use the same tag name as the release.
   - Helm chart versions need to be updated according to the `version:` field value found in each chart's `Chart.yaml` file in the tagged version of the repository.
