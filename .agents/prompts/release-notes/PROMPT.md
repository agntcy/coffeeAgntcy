# Release notes generation

## Parameters

Read `.agents/prompts/release-notes/params.yaml` and use:

|       Field        |                 Meaning                 |
| ------------------ | --------------------------------------- |
| `previous_version` | Tag/version of the last release         |
| `current_version`  | Version you are writing notes for       |
| `repo_url`         | GitHub repository URL                   |
| `github_repo`      | `owner/name` for links and `gh` queries |

## Task

Generate release notes for `repo_url` covering changes **since** `previous_version` **through** what will ship as
`current_version`.

- Base the diff on merges to the default branch since the `previous_version` tag.
- Use the previous release as a style reference: git tag `previous_version`, and the matching section in repository root
  `CHANGELOG.md`.
- Prefer **PR-level** granularity; do not enumerate individual commits except when a change landed on the default branch
  **without** an associated PR.
- Be concise and practical.

## Output structure

Produce a new `CHANGELOG.md` entry for `current_version` with this structure:

### 1. Title line

```markdown
## {current_version} ({YYYY-MM-DD})
```

Use today's date unless the user specifies another.

### 2. One-line release blurb

Short paragraph highlighting the most important themes of the release.

### 3. Summary

Order of emphasis:

1. Semver **breaking** changes, configuration/setup/interface changes, and breaking behavior changes — **first**.
2. **Migration steps** when any of the above apply; include concrete examples (env vars, commands, config snippets).
3. High-profile new features.

For each highlighted item in this section, use a closed HTML dropdown:

```html
<details>
<summary><strong>Short title</strong> — optional subtitle</summary>

- Concise bullets with links to PRs where relevant.
</details>
```

### 4. Dependency changes

List only dependencies whose versions **changed** since `previous_version`. Do not list unchanged dependencies.

Derive versions from lockfiles and manifests, including as applicable:

- `coffeeAGNTCY/coffee_agents/lungo/uv.lock`
- `coffeeAGNTCY/coffee_agents/corto/uv.lock`
- `coffeeAGNTCY/coffee_agents/recruiter/uv.lock`
- `coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json`
- `coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package-lock.json`

### 5. Changeset (chronological)

List changes in the order they landed on the default branch:

- One line per PR (preferred), or per direct commit when no PR exists.
- Each item uses a **closed** HTML dropdown.
- Closed summary line format: PR title, PR number, and author — e.g. `#601 — @author — short title`.
- Open body: detailed but concise description of what was implemented.

### 6. Contributors

- **First-time contributors**: thank external contributors appearing for the first time in this release.
- **Returning contributors**: thank repeat external contributors.
- **Omit** the internal project crew: @codyhartsook, @delthazor, @jparello, @mihaialexandrescu, @misi-bp, @pregnor.
- If a section would be empty, omit the section **and** its heading.

## Reference files

|          Purpose          |                              Path                               |
| ------------------------- | --------------------------------------------------------------- |
| Style / structure example | `CHANGELOG.md` (see `.agents/prompts/release-notes/example.md`) |
| README dependency format  | `README.md` → `### Built With`                                  |

## Output format (response to the user)

**Do not modify repository files** unless explicitly asked.

Return **two** markdown fenced code blocks:

1. **CHANGELOG entry** — full markdown for the new `## {current_version}` section, ready to paste into `CHANGELOG.md`
   below the `# Changelog` heading.
2. **README Built With** — markdown for the `### Built With` bullet list, matching `README.md` style but with versions
   from the lockfiles above.

If the CHANGELOG entry contains inner markdown code blocks (migration examples), escape inner triple-backticks so the
outer fence does not break.

## Quality bar

Match the tone, structure, and HTML `<details>` usage of the example in `CHANGELOG.md` for release `0.1.1` unless the
user asks otherwise.
