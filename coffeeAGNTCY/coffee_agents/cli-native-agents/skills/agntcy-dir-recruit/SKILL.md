---
name: agntcy-dir-recruit
description: Search the AGNTCY directory for remote A2A agents, present candidates, and connect them to the current CLI-native agent as skills. Use when the user wants to recruit, find, browse, or connect to a new remote agent.
compatibility: Requires dirctl, jq, and a running AGNTCY directory server.
---

# Recruit — Agent Discovery and Connection

Search the AGNTCY directory for remote A2A agents, present candidates, and connect them to the current CLI-native agent as **skills**.

**Usage:** `/recruit [natural language description of what agent you need]`

**Examples:**
- `/recruit` — browse all available agents
- `/recruit I need an agent that can tell me coffee farm yields` — targeted search
- `/recruit Find me a code review agent` — targeted search

> **Host invocation note:** Examples below use the Claude Code `/skill-name` slash-command syntax and `$ARGUMENTS` substitution. Other CLI-native agent hosts may invoke skills differently — adapt as needed.

---

## Instructions

You are a dynamic agent recruiter. Search the AGNTCY directory, present candidates, and create skill files for the user's selections. Follow these steps.

---

### Step 0 — Resolve the project skill directory

Before searching or creating skills, load the project config written by `cli-native-agents/install.sh`. This exports `AGNTCY_SKILLS_DIR` (where generated skills go) and `AGNTCY_A2A_SEND` (the bundled a2a-send binary).

```bash
. "$(pwd)/.agntcy/cli-native-agents/env.sh" || exit 1
```

If sourcing fails, the helper prints a clear error pointing at `install.sh`. After sourcing, use `"$AGNTCY_SKILLS_DIR"` for every skill lookup and write in this command. Pre-set environment variables (e.g. `AGNTCY_SKILLS_DIR=/tmp/foo`) override the config file — useful for testing.

Do **not** hard-code any host-specific skills directory in generated commands. Always use `"$AGNTCY_SKILLS_DIR"`.

---

### Step 1 — Search the directory

Parse the skill arguments to determine search mode and run `dirctl search`.

**Intent:**
- Empty / "all" / "list" / "browse" → **Browse**: `dirctl search --skill "*"`
- Specific request → **Targeted**: translate to flags using the table below

**NL-to-flags guide:**

| User says | dirctl flags |
|-----------|-------------|
| A skill or capability | `--skill "<keyword>"` or `--skill "*<keyword>*"` |
| A domain or industry | `--domain "*<keyword>*"` |
| A specific agent name | `--name "*<keyword>*"` |
| Something vague | `--skill "*"` then filter by description client-side |

**Run the search:**
```bash
dirctl search --skill "<keyword>"
```

This returns **CIDs** (Content Identifiers) — short strings, one per matching agent. Example output:
```
Record CIDs found: [baeareicbymfgll4l3ngwbfkg7k5o2if5fajfu7beswvwe7r2yv3cmkvf5a ...]
```

Parse the CID strings from the output. If no CIDs are found, try a broader search (`--skill "*"`). If still nothing, tell the user no agents were found.

**Cap:** Pull at most **20 CIDs** to keep things fast. If more are returned, take the first 20 and inform the user.

---

### Step 2 — Pull records and present candidates

For each CID, pull the full OASF record and extract a summary:

```bash
mkdir -p ./tmp
dirctl pull <CID> --output json > ./tmp/recruit_<N>.json
```

Then extract the fields we need with one jq filter:

```bash
jq '{
  name: .name,
  description: .description,
  endpoint: (
    ( [ .modules[]
        | select(.name=="integration/a2a")
        | .data.card_data.supportedInterfaces[]?
        | select((.protocolBinding // "" | ascii_downcase) | . == "slim" or . == "slimrpc")
        | "slim://" + .url
      ] | first )
    // (.modules[] | select(.name=="integration/a2a") | .data.card_data.url)
  ),
  transport: (
    if [ .modules[]
         | select(.name=="integration/a2a")
         | .data.card_data.supportedInterfaces[]?
         | select((.protocolBinding // "" | ascii_downcase) | . == "slim" or . == "slimrpc")
       ] | length > 0
    then "slim" else "http" end
  ),
  skills: [(.modules[] | select(.name=="integration/a2a") | .data.card_data.skills[]? | {name: .name, description: .description})],
  protocolVersion: (.modules[] | select(.name=="integration/a2a") | .data.card_data.protocolVersion),
  provider: ((.modules[] | select(.name=="integration/a2a") | .data.card_data.provider.organization) // "")
}' ./tmp/recruit_<N>.json
```

The `endpoint` value is **scheme-prefixed**:
- `slim://org/ns/name` for SLIM agents (extracted from `supportedInterfaces[]` with `protocolBinding` of `slim` or `slimrpc`),
- `http(s)://host:port` for HTTP agents (from `card_data.url`).

The bundled `a2a-send` binary detects transport from this prefix at invocation time, so generated skills don't need to branch on transport themselves.

If the jq filter fails for a record (missing A2A module, unexpected structure), skip it and note the skip.

**Check for existing skills** (use `find`, not `ls` with globs — zsh's `nomatch` setting will fail the whole command if a glob matches nothing):
```bash
find "$AGNTCY_SKILLS_DIR" -name SKILL.md 2>/dev/null
```

---

### Step 2.5 — Verify record signatures

For each pulled CID, run `dirctl verify` to check that the OASF record is signed by a trusted publisher. This is a local Sigstore-based trust check — it does **not** talk to the identity service (that comes later via `/check-identity`).

```bash
dirctl verify <CID> --output raw 2>&1
```

**Important parsing notes:**
- `dirctl verify` runs **local** Sigstore verification by default. Do **not** pass `--from-server` — most directory servers return `Unimplemented` for cached verification.
- The exit code is **0 in both signed and unsigned cases** (it indicates "verification ran," not "record is trusted"). You must parse the output.
- `--output raw` gives:
  - empty stdout → **`signed ✓`** (trusted)
  - `error_message:"<reason>"` → **`unsigned ✗`** (use the reason as the warning detail; `"no signatures found"` is the common case)

If `dirctl verify` is not available in the user's environment, or it errors out (e.g. directory server unreachable), skip this step entirely and render the table without the Verified column — note the skip once, do not error out.

---

### Step 2.6 — Present candidates

**Present a table** (with the new Verified column from Step 2.5):

```
## Available Agents

| # | Name | Description | Skills | Transport | Endpoint | Verified | Status |
|---|------|-------------|--------|-----------|----------|----------|--------|
| 1 | CoffeeFarmAgent | Coffee yield analysis | Get Coffee Yield | http | http://0.0.0.0:9999 | signed ✓ | new |
| 2 | Hello World Agent | Just a hello world agent | Hello, world! | slim | slim://agntcy/foundry/gateway | signed ✓ | new |
| 3 | ReviewBot | Code review | code_analysis | http | http://0.0.0.0:7777 | unsigned ✗ | [exists] |
```

- **Description**: truncate to ~80 chars
- **Skills**: comma-separated skill names
- **Transport**: `http` or `slim` (from the jq `transport` field)
- **Endpoint**: the scheme-prefixed value from the jq `endpoint` field (this is what gets pasted into the skill as `--peer-url`)
- **Verified**: `signed ✓` / `unsigned ✗` from Step 2.5 (omit column if dirctl verify was skipped)
- **Status**: `new` or `[exists]` if a skill already exists for that agent name

**Selection prompt:**
```
Pick agents to connect:
  • Numbers: 1,3,5 or ranges: 1-3
  • "all" — all new agents (skips existing)
  • "none" — just browsing
```

**`all` selection warning:** if any selected candidates are `unsigned ✗`, list them and confirm before proceeding:

```
⚠ The following selected agents are unsigned:
  - ReviewBot (unsigned ✗): <stderr reason from dirctl verify>

Continue with these unsigned agents? (y/n)
```

For numeric selection, do not prompt — the user has explicitly picked.

If the user declines — stop here.

> **Note:** A `signed ✓` record means the OASF record itself is signed. It does **not** confirm the agent has a valid identity-service badge or any policies. After creating the skill, run `/check-identity <name>` to inspect the badge and policies.

---

### Step 3 — Create skills

For each selected agent, **immediately** do the following without asking further questions:

**3a. Generate name:** Lowercase the agent name, replace spaces/special chars with hyphens. Example: "Brazil Coffee Farm" → `brazil-coffee-farm`

**3b. Create the skill directory and write the SKILL.md by copying the template.**

Generated skills load `$AGNTCY_A2A_SEND` at invoke time via the `env.sh` helper, so the template only needs three substitutions: `__SKILL_NAME__`, `__AGENT_DISPLAY_NAME__`, and `__ENDPOINT__`. Everything else stays literal (the `$ARGUMENTS` token, the `env.sh` sourcing line).

Run **one** Bash invocation per skill, substituting `<name>`, `<endpoint>`, and `<agent-display-name>` with the values for the selected agent:

```bash
mkdir -p "$AGNTCY_SKILLS_DIR/<name>"
sed \
  -e "s|__SKILL_NAME__|<name>|g" \
  -e "s|__AGENT_DISPLAY_NAME__|<agent-display-name>|g" \
  -e "s|__ENDPOINT__|<endpoint>|g" \
  "$AGNTCY_SKILLS_DIR/a2a-messaging/scripts/a2a-send/skill-template.md" \
  > "$AGNTCY_SKILLS_DIR/<name>/SKILL.md"
```

Notes:
- `sed` uses `|` as the delimiter so URLs (which contain `/`) need no escaping.
- If `<agent-display-name>` contains a literal `|` or `&`, escape it before substitution (`\|`, `\&`). `"`, `'`, and spaces are fine.

Verify by `cat`ing the resulting file and confirming:
- `$ARGUMENTS` still appears literally (dollar sign intact).
- The `env.sh` sourcing line is present near the top.
- The three placeholders were replaced with the agent's actual values.

**3c. Clean up and summarize:**

```bash
rm -f ./tmp/recruit_*.json
```

```
## Skills Created

| Skill | Agent | Transport | Endpoint | Invoke with |
|-------|-------|-----------|----------|-------------|
| /brazil-coffee-farm | Brazil Coffee Farm | http | http://0.0.0.0:9999 | /brazil-coffee-farm <message> |
| /hello-world-agent | Hello World Agent | slim | slim://agntcy/foundry/gateway | /hello-world-agent <message> |

Skills are available immediately — no restart needed.
Example: `/brazil-coffee-farm What is the current yield?`

**If any generated skills use the `slim` transport**, also note:
- `SLIM_SHARED_SECRET` must be exported in the environment (must match the value the remote agent was started with).
- `SLIM_ENDPOINT` defaults to `http://127.0.0.1:46357`; override if your SLIM node lives elsewhere.

To inspect the agent's identity-service badge and policies, run:
`/check-identity brazil-coffee-farm`
```

---

## Error Handling

- **dirctl not found**: Tell user to install dirctl and ensure it's in PATH
- **No directory server**: Set `DIRECTORY_CLIENT_SERVER_ADDRESS` env var (default `0.0.0.0:8888`). Run `dirctl info` to verify
- **No agents found**: Suggest broader search terms or check that agents are registered
- **jq filter fails on a record**: Skip that record, note it, continue with others
- **File write failure**: Check permissions on `$AGNTCY_SKILLS_DIR`
