# Recruit — Agent Discovery and Connection

Search the AGNTCY directory for remote A2A agents, present candidates, and connect them to Claude Code — either as **skills** (recommended) or **sub-agents**.

**Usage:** `/recruit [natural language description of what agent you need]`

**Examples:**
- `/recruit` — browse all available agents
- `/recruit I need an agent that can tell me coffee farm yields` — targeted search
- `/recruit Find me a code review agent` — targeted search

---

## Instructions

You are a dynamic agent recruiter. Search the AGNTCY directory, present candidates, and create skill or sub-agent files for the user's selections. Follow these steps.

---

### Step 1 — Search the directory

Parse `$ARGUMENTS` to determine search mode and run `dirctl search`.

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
dirctl pull <CID> --output json > ./tmp/recruit_<N>.json
```

Then extract the fields we need with one jq filter:

```bash
jq '{
  name: .name,
  description: .description,
  endpoint: (.modules[] | select(.name=="integration/a2a") | .data.card_data.url),
  skills: [(.modules[] | select(.name=="integration/a2a") | .data.card_data.skills[]? | {name: .name, description: .description})],
  protocolVersion: (.modules[] | select(.name=="integration/a2a") | .data.card_data.protocolVersion),
  provider: ((.modules[] | select(.name=="integration/a2a") | .data.card_data.provider.organization) // "")
}' ./tmp/recruit_<N>.json
```

If the jq filter fails for a record (missing A2A module, unexpected structure), skip it and note the skip.

**Check for existing skills and sub-agents:**
```bash
ls .claude/skills/*/SKILL.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
```

**Present a table:**

```
## Available Agents

| # | Name | Description | Skills | Endpoint | Status |
|---|------|-------------|--------|----------|--------|
| 1 | CoffeeFarmAgent | Coffee yield analysis | Get Coffee Yield | http://0.0.0.0:9999 | new |
| 2 | ReviewBot | Code review | code_analysis | http://0.0.0.0:7777 | [exists] |
```

- **Description**: truncate to ~80 chars
- **Skills**: comma-separated skill names
- **Status**: `new` or `[exists]` if a skill or sub-agent already exists for that agent name

**Selection prompt:**
```
Pick agents to connect:
  • Numbers: 1,3,5 or ranges: 1-3
  • "all" — all new agents (skips existing)
  • "none" — just browsing
```

If the user declines — stop here.

---

### Step 3 — Choose creation mode

Ask the user how to create the recruited agents:

```
How should the recruited agents be created?

  • skill (Recommended) — Creates a /slash-command. The parent model runs the
    a2a-send command directly. More reliable — guaranteed to forward all requests.
    Invoke with: /agent-name <message>

  • subagent — Creates a sub-agent file. A separate model is spawned to handle
    requests. Note: sub-agent models may refuse to forward requests they deem
    outside the agent's advertised capabilities, even when the remote agent can
    handle them.
```

Default to **skill** if the user doesn't have a preference.

---

### Step 4A — Create skills (if skill mode chosen)

For each selected agent, **immediately** do the following without asking further questions:

**4A-a. Generate name:** Lowercase the agent name, replace spaces/special chars with hyphens. Example: "Brazil Coffee Farm" → `brazil-coffee-farm`

**4A-b. Create the skill directory and write the SKILL.md using the Write tool:**

First get the absolute project path and create the skill directory:
```bash
pwd
mkdir -p .claude/skills/{name}
```

Then use the **Write tool** to write the SKILL.md file. The Write tool requires an **absolute path** — use the output of `pwd` above to construct it: `<pwd output>/.claude/skills/{name}/SKILL.md`. Do NOT use a relative path. Fill ALL `{placeholders}` below with actual values from the pulled record. The file must be fully self-contained with zero unresolved placeholders.

**IMPORTANT:** Write the file exactly as specified below. Do NOT modify the generated file afterwards — every field in the frontmatter (including `allowed-tools`) is intentional and required for correct behavior.

**File contents to write:**

```
---
name: {name}
description: "Send a message to the remote {agent_display_name} agent via A2A protocol. Use for ANY request intended for this agent — the remote agent determines what it can handle."
allowed-tools: Bash
---

## EXECUTE NOW

Run this command to send the user's message to the remote A2A agent:

\`\`\`bash
plugin/scripts/a2a-send/a2a-send --peer-url {endpoint} --message "$ARGUMENTS"
\`\`\`

- stdout contains the agent's response
- If exit code 1, stderr contains a JSON error — relay the error to the user
- For long-running tasks, add --non-blocking --wait flags
```

**4A-c. Clean up and summarize:**

```bash
rm -f ./tmp/recruit_*.json
```

```
## Skills Created

| Skill | Agent | Endpoint | Invoke with |
|-------|-------|----------|-------------|
| /brazil-coffee-farm | Brazil Coffee Farm | http://0.0.0.0:9999 | /brazil-coffee-farm <message> |

Skills are available immediately — no restart needed.
Example: `/brazil-coffee-farm What is the current yield?`
```

---

### Step 4B — Create sub-agents (if subagent mode chosen)

Ask the user which model to use (default **haiku**):

| Model | Best for |
|-------|----------|
| **haiku** (Recommended) | Simple request-response agents, fast + cheap |
| **sonnet** | Complex multi-turn, reasoning-heavy agents |
| **opus** | Deep analysis or long context |

Then for each selected agent, **immediately** do the following without asking further questions:

**4B-a. Generate filename:** Lowercase the agent name, replace spaces/special chars with hyphens, append `.md`. Example: "Brazil Coffee Farm" → `brazil-coffee-farm.md`

**4B-b. Create the directory and write the file using the Write tool:**

First get the absolute project path and create the agents directory:
```bash
pwd
mkdir -p .claude/agents
```

Then use the **Write tool** to write each file. The Write tool requires an **absolute path** — use the output of `pwd` above to construct it: `<pwd output>/.claude/agents/<filename>`. Do NOT use a relative path. Fill ALL `{placeholders}` below with actual values from the pulled record. The file must be fully self-contained with zero unresolved placeholders.

**File contents to write:**

```
---
name: {filename_without_extension}
description: "{agent_display_name} remote agent. Dispatch this agent for any request related to this agent."
model: {selected_model}
tools: Bash
---

You cannot answer any questions yourself. You have no information about anything. You must use the Bash tool to query a remote system for every single request — without running the command, you have absolutely nothing to tell the user.

Run this command for EVERY request (replace MESSAGE with the user's exact words, shell-escaped):

\`\`\`bash
plugin/scripts/a2a-send/a2a-send --peer-url {endpoint} --message "MESSAGE"
\`\`\`

Return stdout verbatim. If exit code 1, return stderr. Never add commentary or opinions.
```

**4B-c. Clean up and summarize:**

```bash
rm -f ./tmp/recruit_*.json
```

```
## Sub-Agents Created

| File | Agent | Model | Endpoint | Status |
|------|-------|-------|----------|--------|
| .claude/agents/brazil-coffee-farm.md | Brazil Coffee Farm | haiku | http://0.0.0.0:9999 | created |

**Important:** Run `/exit` and restart Claude Code to reload subagents.
Then invoke naturally: "Use the brazil-coffee-farm agent to check the yield"

> **Note:** Sub-agent models may refuse to forward requests they consider outside the agent's
> advertised capabilities, even when the remote agent can handle them. If you experience this,
> delete the sub-agent file and re-run `/recruit` to create a **skill** instead.
```

---

## Error Handling

- **dirctl not found**: Tell user to install dirctl and ensure it's in PATH
- **No directory server**: Set `DIRECTORY_CLIENT_SERVER_ADDRESS` env var (default `0.0.0.0:8888`). Run `dirctl info` to verify
- **No agents found**: Suggest broader search terms or check that agents are registered
- **jq filter fails on a record**: Skip that record, note it, continue with others
- **File write failure**: Check permissions on `plugin/skills/` or `.claude/agents/`
