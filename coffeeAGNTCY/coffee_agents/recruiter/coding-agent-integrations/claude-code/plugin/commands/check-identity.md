# Check Identity — Inspect badge & policies for a recruited agent

Inspect the AGNTCY identity-service badge and policies attached to a skill or sub-agent created by `/recruit`. This is a **post-recruit, on-demand** check — it does not run automatically on send.

**Usage:** `/check-identity <skill-or-subagent-name>`

**Examples:**
- `/check-identity brazil-coffee-farm`
- `/check-identity review-bot`

---

## Prerequisites

The plugin's identity client reads two env vars:

| Var | Purpose |
|-----|---------|
| `IDENTITY_API_SERVER_URL` | e.g. `http://0.0.0.0:4000` |
| `IDENTITY_SERVICE_API_KEY`  | API key for the calling service (`x-id-api-key`) |

If either is unset, stop and tell the user to set them (point at `coffee_agents/recruiter/.env.example` for reference values).

---

## Instructions

### Step 1 — Resolve the target file

Parse `$ARGUMENTS` to get `<name>`. Look for the corresponding file in this order:

```bash
.claude/skills/<name>/SKILL.md
.claude/agents/<name>.md
```

If neither exists, list what does exist (`ls .claude/skills/ .claude/agents/`) and stop.

### Step 2 — Extract endpoint and display name

From the resolved file:

- **Endpoint URL**: parse the `--peer-url <url>` value out of the `a2a-send` command line.
- **Display name**: pull from the `description:` frontmatter (the human-readable agent name in the description, e.g. `"Brazil Coffee Farm"` from `"Send a message to the remote Brazil Coffee Farm agent..."`). If you can't reliably extract it, fall back to the `<name>` slug.

If the endpoint cannot be extracted, stop with an error.

### Step 3 — Resolve app_id from the identity service

Run:

```bash
"$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/identity_client.py" apps
```

Parse the JSON. The shape is `{"apps": [{"id": "...", "name": "...", ...}, ...]}`.

Match strategy:
1. **Exact match** on `app.name == <display_name>` (case-insensitive).
2. If zero or multiple exact matches, fall back to **fuzzy contains** (`<display_name>` substring of `app.name` or vice versa, case-insensitive).
3. If still zero or multiple, print the candidate list (just `id` and `name` of every app) and stop — let the user pick and re-run with a more specific name.

Capture the matched `app_id`.

### Step 4 — Verify the badge

```bash
"$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/identity_client.py" verify --app-id <app_id>
```

Possible outcomes:
- **Exit 0**: badge fetched and verified. Output is `{"app_id":..., "badge":..., "verification":...}`.
- **Exit 1, stderr says `HTTP 404`**: no badge issued for this app. Treat as a clean "no badge" result, not an error — continue to Step 6 with `Badge: ✗ none issued` and skip Step 5.
- **Exit 1, any other error**: render `Badge: ⚠ verification failed (<error>)` and skip Step 5.

### Step 5 — List policies targeting this app

Only run if Step 4 returned a verified badge.

```bash
"$(command -v python3 || command -v python)" "${CLAUDE_PLUGIN_ROOT}/scripts/identity_client.py" policies --app-id <app_id>
```

The script filters policies client-side to those whose `rules[].tasks[].appId == <app_id>` or whose `assignedTo` contains the app id. For each matching policy, collect: `id`, `name`, the rule `action` values, `needsApproval` (any rule that sets it true), and the tasks that target this app (`name` + `toolName` if present).

### Step 6 — Render the report

```
## Identity check: <name>

App:        <display_name>  (id: <app_id>)
Endpoint:   <endpoint>
Badge:      <status>
Policies:   <N attached>

- [<action>]  <policy_name>           needsApproval=<true|false>
              tasks: <task_name>(<toolName>), ...
```

Status legend:
- `✓ verified`
- `✗ none issued`
- `⚠ verification failed (<reason>)`

If no policies match, print `Policies:   none attached` and skip the bullet list.

---

## Error handling

| Symptom | Cause / message |
|---------|-----------------|
| `IDENTITY_API_SERVER_URL is not set` (stderr from script) | Tell user to export both env vars; point at `coffee_agents/recruiter/.env.example`. |
| `HTTP 401` / `HTTP 403` | API key missing, wrong, or not authorized for this service. |
| `HTTP 404` on badge | Treat as "no badge issued" — render cleanly, exit 0. |
| `Connection error` | Identity service not reachable at `IDENTITY_API_SERVER_URL`. |
| Multiple/zero app_id matches | List candidates, ask user to re-run with a more specific name. |

---

## Notes

- This command does **not** modify the skill or sub-agent file. It's read-only inspection.
- `/check-identity` does not enforce anything at runtime — calls made via the recruited skill or sub-agent are unaffected by the result. Use this command before relying on an agent for sensitive work.
- The matching `dirctl verify` step (during `/recruit`) and this command are independent: signed records can be missing badges, and apps with badges can be in unsigned records. Consider both signals.
