# Changelog

## 0.2.0 (2026-06-25)

Fiber milestone: **Open UI Kit frontend**, **SLIM 1.4 upgrade** (Lungo + Corto), **MCP live workflow events**, **pattern reference library chat**, **A2A transport rails** on agent nodes, and **recruiter flow optimizations**.

### Summary

**Breaking / migration (read first)**

<details>
<summary><strong>Lungo UI — Open UI Kit migration</strong> — Tailwind removed; Node.js ≥ 24 required</summary>

- Full frontend restyle on **`@open-ui-kit/core`** + MUI; **Tailwind CSS**, PostCSS, and related utility deps removed ([#614](https://github.com/agntcy/coffeeAgntcy/pull/614)).
- **`frontend/package.json`** requires **`node >= 24.0.0`** and **`npm >= 11.10.1`**; run **`npm ci`** after pull.
- Custom UI work should use Open UI Kit / MUI tokens — not Tailwind classes.
</details>

<details>
<summary><strong>SLIM 1.4.0</strong> — Helm, Python bindings, Corto + Lungo agents</summary>

- SLIM Helm dependency **v0.6.0 → v1.4.0**; **`slim-bindings`** **1.1.0 → 1.4.0** in Lungo/Corto lockfiles ([#665](https://github.com/agntcy/coffeeAgntcy/pull/665)).
- Updates agent cards, A2A transport config, Compose, and Helm transport secrets across **Lungo and Corto**.
- Refresh **`lungo/.env`**, **`corto/.env`**, and rebuild agent images after upgrade.
</details>

<details>
<summary><strong>Helm chart bumps</strong> — <code>lungo-local-cluster@0.5.0</code>, <code>lungo-ui@0.1.4</code>, subcharts <code>0.1.2</code></summary>

- Umbrella **`lungo-local-cluster`** **0.4.1 → 0.5.0**; **`lungo-ui`** **0.1.2 → 0.1.4** (via [#645](https://github.com/agntcy/coffeeAgntcy/pull/645), [#614](https://github.com/agntcy/coffeeAgntcy/pull/614), [#662](https://github.com/agntcy/coffeeAgntcy/pull/662)).
- All Lungo agent/MCP subcharts **0.1.1 → 0.1.2**; **`agentic-workflows-api@0.1.1`**.
- Deployment **tolerations** added to Lungo and Corto Helm charts ([#647](https://github.com/agntcy/coffeeAgntcy/pull/647)).
- Run **`helm dependency update`** under **`deployment/helm/local-cluster`** (and Corto umbrella) before upgrading.
</details>

<details>
<summary><strong>Recruiter agent</strong> — App SDK JSONRPC transport and directory search batching</summary>

- Recruiter aligns with Lungo **A2A client** usage; agent cards use canonical **JSONRPC** transport metadata ([#655](https://github.com/agntcy/coffeeAgntcy/pull/655)).
- Directory registry search is batched; bundled **dirctl** bumped to **v1.5.0** for export support.
- Rebuild recruiter images / refresh **`recruiter/uv.lock`** on upgrade.
</details>

<details>
<summary><strong>Pattern chat API</strong> — optional LiteLLM proxy for <code>POST /patterns/{name}/chat</code></summary>

- New docs-grounded pattern advisor endpoint ([#651](https://github.com/agntcy/coffeeAgntcy/pull/651)).
- For proxy-backed models, set **`LITELLM_PROXY_BASE_URL`** and **`LITELLM_PROXY_API_KEY`** in **`lungo/.env`** (see **`.env.example`**).
</details>

**Migration steps**

1. Refresh env templates:

       cp coffeeAGNTCY/coffee_agents/lungo/.env.example coffeeAGNTCY/coffee_agents/lungo/.env
       cp coffeeAGNTCY/coffee_agents/lungo/frontend/.env.example coffeeAGNTCY/coffee_agents/lungo/frontend/.env
       cp coffeeAGNTCY/coffee_agents/corto/.env.example coffeeAGNTCY/coffee_agents/corto/.env

2. **Frontend dev:** use **Node.js ≥ 24**, then:

       cd coffeeAGNTCY/coffee_agents/lungo/frontend
       npm ci

3. **Helm / KinD:** **`helm dependency update`** in **`deployment/helm/local-cluster`**, upgrade to **`lungo-local-cluster@0.5.0`**, then reinstall/upgrade the release.

4. **Docker Compose:** rebuild UI and agents after SLIM/dependency bumps:

       docker compose --profile frontend up --build

5. **Recruiter (optional):** rebuild the recruiter service if you run the recruit workflow standalone or via Compose.

**Highlights**

<details>
<summary><strong>MCP live workflow events</strong> — transient tool-call topology in the UI graph</summary>

- **`EventEmittingMCPClient`** wraps MCP **`call_tool`** to emit CREATE/DELETE topology fragments correlated with A2A events ([#630](https://github.com/agntcy/coffeeAgntcy/pull/630), closes [#587](https://github.com/agntcy/coffeeAgntcy/issues/587)).
- Colombia farm and weather MCP paths instrumented; documented in **`docs/a2a_event_schema_middleware.md`**.
- Controlled by existing **`EMIT_WORKFLOW_EVENTS`**; no emission when identity cannot be resolved.
</details>

<details>
<summary><strong>Pattern reference library</strong> — backend chat + frontend explorer canvas</summary>

- **`POST /patterns/{name}/chat`** streams a docs-grounded pattern advisor; FE pattern explorer with resizable doc/chat panels and Mermaid rendering ([#651](https://github.com/agntcy/coffeeAgntcy/pull/651), [#652](https://github.com/agntcy/coffeeAgntcy/pull/652)).
</details>

<details>
<summary><strong>A2A transport rail</strong> — per-agent transport interfaces on graph nodes</summary>

- Agent nodes render an expandable **transport rail** showing available transports and highlighting the active/preferred one from OASF card metadata ([#664](https://github.com/agntcy/coffeeAgntcy/pull/664)).
</details>

<details>
<summary><strong>Workflow graph animations</strong> — broadcast-type prompt events</summary>

- UI pulses graph nodes for **broadcast-type** workflow events, not only direct agent prompts ([#643](https://github.com/agntcy/coffeeAgntcy/pull/643)).
</details>

<details>
<summary><strong>UI polish</strong> — chat area, sidebar, and graph styling</summary>

- Chat area backgrounds, sidebar hierarchy/indentation, collapse control placement, and graph node sizing refinements ([#662](https://github.com/agntcy/coffeeAgntcy/pull/662)).
</details>

### Dependencies

| Component | 0.1.2 | 0.2.0 |
| --- | --- | --- |
| `lungo-local-cluster` Helm chart | 0.4.1 | **0.5.0** |
| SLIM Helm chart | v0.6.0 | **v1.4.0** |
| `lungo-ui` Helm chart | 0.1.2 | **0.1.4** |
| Lungo agent/MCP subcharts | 0.1.1 | **0.1.2** |
| `agentic-workflows-api` subchart | 0.1.0 | **0.1.1** |

**Lungo** (`lungo/uv.lock`):

| Package | 0.1.2 | 0.2.0 |
| --- | --- | --- |
| `langgraph` | 1.0.7 | **1.2.2** |
| `mcp` | 1.26.0 | **1.27.1** |
| `slim-bindings` | 1.1.0 | **1.4.0** |

Unchanged from 0.1.2 in Lungo: `agntcy-app-sdk` 0.5.5, `a2a-sdk` 0.3.20, `ioa-observe-sdk` 1.0.41, `agntcy-identity-service-sdk` 0.0.7.

**Recruiter** (`recruiter/uv.lock`): `agntcy-app-sdk` 0.4.6 → **0.5.5**, `a2a-sdk` 0.3.2 → **0.3.20**, `langgraph` 1.0.5 → **1.2.1**, `mcp` 1.24.0 → **1.27.1**, `slim-bindings` 0.6.3 → **1.1.0**.

**Lungo frontend** (`frontend/package-lock.json`): adds **`@open-ui-kit/core@^1.6.0`**; removes Tailwind stack; **`react@^19.1.0`**.

**Corto** (`corto/uv.lock`): aligned with Lungo on core AGNTCY pins (`agntcy-app-sdk` 0.5.5, `a2a-sdk` 0.3.20, `slim-bindings` 1.4.0, `ioa-observe-sdk` 1.0.41).

### Built With

(Versions from `coffeeAGNTCY/coffee_agents/lungo/uv.lock` and `lungo/frontend/package-lock.json`.)

- [AGNTCY App SDK](https://github.com/agntcy/app-sdk) = v0.5.5
- [SLIM](https://github.com/agntcy/slim) = v1.4.0
- [NATS](https://github.com/nats-io/nats-server) = latest
- [A2A](https://github.com/a2aproject/a2a-python) = v0.3.20
- [MCP](https://github.com/modelcontextprotocol/python-sdk) = v1.27.1
- [LangGraph](https://github.com/langchain-ai/langgraph) = v1.2.2
- [Observe SDK](https://github.com/agntcy/observe) = 1.0.41
- [AGNTCY Identity Service SDK](https://github.com/agntcy/identity-service) = 0.0.7
- [AGNTCY Directory](https://github.com/agntcy/dir) = v1.0.0

### Changeset

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/642">#642</a> — @pregnor — fix(lungo,helm,ui): fix configmap loading</summary>

- Removes a redundant ConfigMap volume mount from the **`lungo-ui`** deployment template that broke runtime **`env-config.js`** loading.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/644">#644</a> — @mihaialexandrescu — chore: do not trigger pytest on frontend changes</summary>

- Limits backend pytest CI to Python paths so frontend-only PRs skip the Lungo test workflow.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/645">#645</a> — @pregnor — release(lungo,ui,helm): bump chart to release chart fix</summary>

- Bumps **`lungo-ui`** Helm chart **0.1.2 → 0.1.3** ahead of the Open UI Kit release train.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/647">#647</a> — @pregnor — Feat/chart deployment tolerations</summary>

- Adds optional **`tolerations`** blocks to Lungo and Corto Helm deployment templates (all agent/MCP/UI subcharts).
- Bumps affected subchart patch versions for release.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/614">#614</a> — @misi-bp — refactor(full UI): Migrate from Tailwind to Open UI Kit</summary>

- Replaces Tailwind with **`@open-ui-kit/core`** across the Lungo UI; drops Tailwind/PostCSS toolchain.
- Requires **Node.js ≥ 24**; bumps Helm **`lungo-ui@0.1.4`** and umbrella chart dependencies.
- Large component restyle: layout, chat, graph, workflow views, and shared theming.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/643">#643</a> — @mihaialexandrescu — fix(lungo): workflow event animations for broadcast-type prompts</summary>

- Extends **`useAgentAPI`** so broadcast/group workflow events pulse the correct graph nodes in the UI.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/630">#630</a> — @delthazor — (feat) Implement MCP live event processing</summary>

- Adds **`common/mcp_event_middleware/`** with **`wrap_mcp_client`** / **`EventEmittingMCPClient`** for transient MCP tool-call topology events.
- Extends **`common/workflow_utils/mcp.py`** builders; instruments Colombia farm MCP path; unit and integration tests.
- Updates **`docs/a2a_event_schema_middleware.md`** for MCP lifecycle (CREATE on start, DELETE on end).
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/652">#652</a> — @codyhartsook — docs(#588): add agent interaction mermaid diagrams to workflow docs</summary>

- Embeds Mermaid sequence diagrams in pattern/workflow documentation for agent interaction flows.
- FE pattern doc viewer renders diagrams with theme-aware edge colors.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/651">#651</a> — @codyhartsook — feat(#588): pattern reference library explorer — BE chat + FE canvas</summary>

- OpenAPI **`POST /patterns/{name}/chat`** with streaming ADK/LiteLLM pattern advisor backed by reference markdown.
- FE pattern explorer: resizable doc/chat panels, **`usePatternChatAPI`**, Mermaid in docs, GitHub doc links.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/665">#665</a> — @pregnor — chore(dep): upgrade SLIM to 1.4.0</summary>

- Bumps SLIM Helm dependency to **v1.4.0** and **`slim-bindings`** across Lungo and Corto **`uv.lock`** files; updates root **Built With**.
- Refactors Corto exchange/farm agents to shared **`a2a_transport_config`**; adds Helm transport secrets and Compose wiring.
- Updates Lungo farm agent cards and integration tests for SLIM 1.4 transport metadata.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/662">#662</a> — @misi-bp — feat: UI improvements from John</summary>

- Chat area and sidebar visual polish (backgrounds, typography, collapse control, parent category selection).
- Graph node sizing/position fixes; Helm subchart version bumps for UI deployment.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/664">#664</a> — @codyhartsook — feat(lungo): A2A transport rail on agent nodes</summary>

- **`TransportRail`** component on graph nodes shows transport interfaces from OASF metadata.
- Highlights active or preferred transport; expands to show transport names on hover/click.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/655">#655</a> — @codyhartsook — Optimize recruiter flow, match lungo a2a client usage, fix card translation</summary>

- Recruiter registry search batched; App SDK JSONRPC transport in agent cards aligned with Lungo.
- Bumps bundled **dirctl** to **v1.5.0**; fixes card translation and directory timeout handling.
- Refreshes **`recruiter/uv.lock`** to current AGNTCY stack pins.
</details>

---

## 0.1.2 (2026-06-09)

Patch release: **runtime UI env injection** for Helm/KinD, **workflow-utils refactor** paving the way for MCP live events (#587), **otel-collector on the default Compose profile**, and **Docker UI build fixes**.

### Summary

**Breaking / migration (read first)**

<details>
<summary><strong>Helm UI runtime env</strong> — <code>window.__ENV__</code> via ConfigMap-mounted <code>env-config.js</code></summary>

- Containerized Lungo UI reads **`VITE_*`** from **`window.__ENV__`** at runtime (before build-time `import.meta.env`).
- Helm chart **`lungo-ui@0.1.2`** renders **`env-config.js`** into a ConfigMap and mounts it at **`/app/dist/env-config.js`**; **`index.html`** loads it before the app bundle ([#613](https://github.com/agntcy/coffeeAgntcy/pull/613), [#620](https://github.com/agntcy/coffeeAgntcy/pull/620)).
- Set **`configs.env.data`** in **`deployment/helm/ui/values.yaml`** (or your umbrella overrides) for every **`VITE_*`** the UI needs — especially **`VITE_AGENTIC_WORKFLOWS_API_KEY`** and service URLs.
- **`npm run dev`** is unchanged: use **`frontend/.env`** as before.
</details>

<details>
<summary><strong>Helm chart bump</strong> — <code>lungo-ui</code> 0.1.1 → 0.1.2</summary>

- Bumps **`lungo-ui`** chart version and fixes ConfigMap mount paths for runtime env ([#620](https://github.com/agntcy/coffeeAgntcy/pull/620)).
- Upgrade UI subchart / run **`helm dependency update`** before deploying.
</details>

<details>
<summary><strong>OTEL collector</strong> — default Compose profile, modular config via env</summary>

- **`otel-collector`** no longer requires the **`observability`** Compose profile or a running ClickHouse instance ([#616](https://github.com/agntcy/coffeeAgntcy/pull/616)).
- Config is split under **`config/docker/otel/`**; defaults use **nop** exporters. Uncomment **`OTELCOL_EXPORTERS_CFG_FILE`** / **`OTELCOL_PIPELINES_CFG_FILE`** in **`lungo/.env`** (see **`.env.example`**) to enable ClickHouse export when the **`observability`** profile is active.
- Refresh **`lungo/.env`** from **`.env.example`** on upgrade.
</details>

<details>
<summary><strong>Docker UI builds</strong> — lockfile discipline and ignore host <code>node_modules</code>/<code>dist</code></summary>

- **`Dockerfile.ui`**: drops redundant **`npm install`**; **`npm run build`** reuses the BuildKit npm cache ([#623](https://github.com/agntcy/coffeeAgntcy/pull/623)).
- Root **`.dockerignore`** excludes **`**/node_modules`** and **`**/dist`** so local macOS artifacts cannot overwrite Linux image layers.
- Rebuild UI images after pull; ensure **`package-lock.json`** is in sync ( **`npm ci`** fails hard if not).
</details>

**Migration steps**

1. Refresh Lungo env templates:

       cp coffeeAGNTCY/coffee_agents/lungo/.env.example coffeeAGNTCY/coffee_agents/lungo/.env
       cp coffeeAGNTCY/coffee_agents/lungo/frontend/.env.example coffeeAGNTCY/coffee_agents/lungo/frontend/.env

2. **Helm / KinD:** upgrade to **`lungo-ui@0.1.2`**, set **`configs.env.data`** for all **`VITE_*`** keys, then upgrade the release.

3. **Docker Compose:** rebuild the UI (and otel-collector if you changed OTEL env vars):

       docker compose --profile frontend up --build

4. **ClickHouse observability (optional):** with the **`observability`** profile, uncomment the **`OTELCOL_*`** ClickHouse lines in **`lungo/.env`** per **`.env.example`**.

**Highlights**

<details>
<summary><strong>Workflow event utilities refactor</strong> — shared <code>workflow_utils</code> for A2A and future MCP emission</summary>

- Extracts builders, event sink, in-flight state, and workflow catalog into **`common/workflow_utils/`**; A2A middleware keeps thin shims ([#615](https://github.com/agntcy/coffeeAgntcy/pull/615), issue [#587](https://github.com/agntcy/coffeeAgntcy/issues/587)).
- No intended runtime behavior change; docs and tests updated (**`docs/a2a_event_schema_middleware.md`**).
</details>

<details>
<summary><strong>Agent skills & DX</strong> — OpenAPI/codegen and release-notes automation</summary>

- OpenAPI → Python / JSON Schema → Pydantic agent skills ([#543](https://github.com/agntcy/coffeeAgntcy/pull/543)).
- Release-notes prompt, skill, and **`AGENTS.md`** index ([#617](https://github.com/agntcy/coffeeAgntcy/pull/617)).
</details>

<details>
<summary><strong>Frontend CI</strong> — consolidated Vitest config and <code>npm run check</code></summary>

- Merges Vitest into **`vite.config.ts`**; FE CI runs **`npm run check`** ([#620](https://github.com/agntcy/coffeeAgntcy/pull/620)).
</details>

<details>
<summary><strong>Supply chain</strong> — smaller, faster UI images</summary>

- Lungo UI image ~**940 MB → ~540 MB**; no-cache build ~**55–65 s → ~30 s** locally ([#623](https://github.com/agntcy/coffeeAgntcy/pull/623)).
</details>

### Dependencies

| Component | 0.1.1 | 0.1.2 |
| --- | --- | --- |
| `lungo-ui` Helm chart | 0.1.1 | **0.1.2** |

Resolved **Python** pins in `lungo/uv.lock` and **npm** pins in `lungo/frontend/package-lock.json` are unchanged from 0.1.1 (`agntcy-app-sdk` 0.5.5, `a2a-sdk` 0.3.20, `ioa-observe-sdk` 1.0.41, `mcp` 1.26.0, `langgraph` 1.0.7).

### Built With

(Versions from `coffeeAGNTCY/coffee_agents/lungo/uv.lock` and `lungo/frontend/package-lock.json`.)

- [AGNTCY App SDK](https://github.com/agntcy/app-sdk) = v0.5.5
- [SLIM](https://github.com/agntcy/slim) = v1.0.0
- [NATS](https://github.com/nats-io/nats-server) = latest
- [A2A](https://github.com/a2aproject/a2a-python) = v0.3.20
- [MCP](https://github.com/modelcontextprotocol/python-sdk) = v1.26.0
- [LangGraph](https://github.com/langchain-ai/langgraph) = v1.0.7
- [Observe SDK](https://github.com/agntcy/observe) = 1.0.41
- [AGNTCY Identity Service SDK](https://github.com/agntcy/identity-service) = 0.0.7
- [AGNTCY Directory](https://github.com/agntcy/dir) = v1.0.0

### Changeset

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/543">#543</a> — @mihaialexandrescu — feat(lungo): add Skill for OpenAPI spec to Python code and Pydantic types</summary>

- Adds agent skills for generating FastAPI routers/DTOs from Lungo OpenAPI specs and Pydantic types from JSON Schema.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/617">#617</a> — @pregnor — chore(repo): add release notes gen prompt/skill</summary>

- Adds **`.agents/prompts/release-notes/`**, **`generate-release-notes`** skill, and **`AGENTS.md`** index for LLM tooling.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/613">#613</a> — @pregnor — fix(lungo,fe): runtime load env</summary>

- UI loads **`VITE_*`** from **`window.__ENV__`** at runtime; Helm ConfigMap renders **`env-config.js`** and mounts it into the UI container.
- Updates **`local-cluster`** values and UI Helm templates for runtime env injection.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/620">#620</a> — @pregnor — fix(lungo,fe,ui,helm): fix small issues</summary>

- Fixes Helm env ConfigMap mount; bumps **`lungo-ui@0.1.2`**.
- Consolidates Vitest into **`vite.config.ts`**; FE CI runs **`npm run check`**; ignores **`*.tsbuildinfo`**.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/615">#615</a> — @delthazor — Initial refactor before MCP event logic</summary>

- Moves shared workflow-event utilities to **`common/workflow_utils/`** with A2A compatibility shims; prepares [#587](https://github.com/agntcy/coffeeAgntcy/issues/587) MCP live-event emission.
- Adds unit tests for builders and updates middleware/catalog tests.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/623">#623</a> — @mihaialexandrescu — feat(lungo, corto): re-tweak Dockerfile.ui</summary>

- Removes redundant **`npm install`**; BuildKit cache for **`npm run build`**; **`.dockerignore`** excludes host **`node_modules`** / **`dist`**.
- Smaller, faster Lungo UI Docker images.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/616">#616</a> — @mihaialexandrescu — feat(lungo): move otel-collector to default docker compose profile</summary>

- **`otel-collector`** runs on the default profile with modular OTEL config files and env-driven exporter/pipeline selection (nop by default; ClickHouse opt-in).
- Documents observability profile as optional; adds health-check extension and ClickHouse **`retry_on_failure`**.
</details>

---

## 0.1.1 (2026-05-28)

Patch release: **authenticated Agentic Workflows API**, **Helm/KinD fixes** for workflows and SLIM, **Colombia farm weather-aware inventory**, and **Docker/supply-chain hardening**.

### Summary

**Breaking / migration (read first)**

<details>
<summary><strong>WORKFLOW_API_KEY</strong> required for Agentic Workflows API and UI</summary>

- Workflow instance **POST**, **GET**, **DELETE**, and internal **POST …/events/** now require a shared secret header.
- **`lungo/.env`**: set `WORKFLOW_API_KEY` (and `WORKFLOW_API_URL` for agents emitting events).
- **`frontend/.env`**: set `VITE_AGENTIC_WORKFLOWS_API_KEY` to the **same** value as the backend key.
- Docker Compose and Helm templates fail fast if the key is unset.
- Introduced in [#571](https://github.com/agntcy/coffeeAgntcy/pull/571); UI chart wiring in [#601](https://github.com/agntcy/coffeeAgntcy/pull/601).
</details>

<details>
<summary><strong>Workflow instance cleanup</strong> — authenticated DELETE endpoint</summary>

- Leaving a workflow view in the UI triggers **DELETE** on the workflow instance so in-memory state is released.
- DELETE uses the same API key as other workflow-instance operations ([#571](https://github.com/agntcy/coffeeAgntcy/pull/571)).
</details>

<details>
<summary><strong>KinD / Helm</strong> — agentic-workflows NodePort 30083 → 30084</summary>

- Avoids a port clash with the Lungo UI service (UI stays on **30083**; API moves to **30084**).
- `lungo-local-cluster` default `agenticWorkflowsApiUrl` is `http://localhost:30084`.
- Part of [#597](https://github.com/agntcy/coffeeAgntcy/pull/597); refresh KinD port-forwards after upgrade.
</details>

<details>
<summary><strong>Helm chart bumps</strong> — ui 0.1.1, local-cluster 0.4.0, service subcharts 0.1.1</summary>

- **`lungo-ui@0.1.1`** — workflow API key passed into the UI build via ConfigMap.
- Lungo agent/MCP/supervisor subcharts **0.1.0 → 0.1.1**; umbrella **`lungo-local-cluster@0.4.0`**.
- **`agentic-workflows-api`** dependency **0.0.2 → 0.1.0**; **`payment-mcp-server@0.1.1`** added to the umbrella chart.
- Run `helm dependency update` under `deployment/helm/local-cluster` before upgrading ([#597](https://github.com/agntcy/coffeeAgntcy/pull/597), [#601](https://github.com/agntcy/coffeeAgntcy/pull/601)).
</details>

<details>
<summary><strong>Dependency age policy</strong> — 28-day minimum for uv and npm</summary>

- **`exclude-newer = "28 days"`** in `[tool.uv]` (Lungo, Corto, Recruiter).
- **`min-release-age=28`** in Lungo/Corto frontend `.npmrc`.
- Brand-new PyPI/npm releases are rejected until they age in ([#559](https://github.com/agntcy/coffeeAgntcy/pull/559)).
</details>

**Migration steps**

1. Set matching workflow API credentials in backend and frontend:

       # lungo/.env
       WORKFLOW_API_KEY=TheAnswerIs42
       WORKFLOW_API_URL=http://agentic-workflows-api:9105

       # frontend/.env
       VITE_AGENTIC_WORKFLOWS_API_KEY=TheAnswerIs42

2. Refresh env templates on upgrade:

       cp coffeeAGNTCY/coffee_agents/lungo/.env.example coffeeAGNTCY/coffee_agents/lungo/.env
       cp coffeeAGNTCY/coffee_agents/lungo/frontend/.env.example coffeeAGNTCY/coffee_agents/lungo/frontend/.env

3. **Helm / KinD:** upgrade to **`lungo-local-cluster@0.4.1`**, run `helm dependency update`, use NodePort **30084** for the API (or port-forward):

       kubectl port-forward svc/lungo-local-cluster-agentic-workflows-api 9105:9105

4. **Docker:** rebuild after pull — root `.dockerignore`, `uv` base images, and BuildKit cache paths changed ([#600](https://github.com/agntcy/coffeeAgntcy/pull/600), [#581](https://github.com/agntcy/coffeeAgntcy/pull/581), [#596](https://github.com/agntcy/coffeeAgntcy/pull/596)):

       docker compose --profile frontend up --build

**Highlights**

<details>
<summary><strong>Authenticated workflow API</strong> — shared key and instance lifecycle</summary>

- End-to-end protection for workflow-instance APIs and UI calls.
- Prevents unauthenticated instance creation and event posts; enables safe cleanup via DELETE ([#571](https://github.com/agntcy/coffeeAgntcy/pull/571)).
</details>

<details>
<summary><strong>Dedicated agentic-workflows ingress</strong> on KinD</summary>

- Agentic Workflows API can be exposed on its own Ingress instead of sharing the UI ingress workaround ([#597](https://github.com/agntcy/coffeeAgntcy/pull/597)).
</details>

<details>
<summary><strong>Colombia farm</strong> — weather MCP drives inventory yield</summary>

- Weather service MCP results are passed into the inventory prompt for weather-aware yield estimates ([#369](https://github.com/agntcy/coffeeAgntcy/pull/369)).
</details>

<details>
<summary><strong>CI stability</strong> — transport socket teardown in tests</summary>

- Test fixtures close transport sockets on teardown to avoid GC warnings that fail CI ([#564](https://github.com/agntcy/coffeeAgntcy/pull/564)).
</details>

<details>
<summary><strong>Supply chain & Docker</strong> — age limits, slimmer context, faster agent builds</summary>

- 28-day minimum package age for `uv` and npm ([#559](https://github.com/agntcy/coffeeAgntcy/pull/559)).
- Root `.dockerignore` ([#600](https://github.com/agntcy/coffeeAgntcy/pull/600)), official `uv` base images ([#581](https://github.com/agntcy/coffeeAgntcy/pull/581)), per-project BuildKit caches ([#596](https://github.com/agntcy/coffeeAgntcy/pull/596)).
- Helm: SLIM shared-secret precedence fix ([#599](https://github.com/agntcy/coffeeAgntcy/pull/599)).
</details>

### Dependencies

| Component | 0.1.0 | 0.1.1 |
| --- | --- | --- |
| `uv` policy (`exclude-newer`, Lungo/Corto/Recruiter) | — | **28 days** |
| npm policy (`min-release-age`, Lungo/Corto frontends) | — | **28 days** |
| `@open-ui-kit/core` (Lungo `package-lock.json`) | 1.4.0 | **1.4.2** |
| `styled-components` (Lungo) | 6.3.11 | **6.4.0** |
| `lodash` (Lungo) | 4.17.23 | **4.18.1** |
| `postcss` (Lungo) | 8.5.6 | **8.5.10** |
| `dompurify` (Lungo) | 3.3.2 | **3.4.0** |
| `follow-redirects` (Lungo) | 1.15.11 | **1.16.0** |
| `lungo-local-cluster` Helm chart | 0.2.0 | **0.4.1** |
| `lungo-ui` Helm chart | 0.1.0 | **0.1.1** |
| Lungo service subcharts (farms, MCP, supervisors, etc.) | 0.1.0 | **0.1.1** |
| `agentic-workflows-api` Helm subchart | 0.0.2 | **0.1.0** |

Resolved **Python** pins in `lungo/uv.lock` are unchanged from 0.1.0 (`agntcy-app-sdk` 0.5.5, `a2a-sdk` 0.3.20, `ioa-observe-sdk` 1.0.41, `mcp` 1.26.0, `langgraph` 1.0.7). The lockfile records the new **28-day** `exclude-newer-span` metadata from [#559](https://github.com/agntcy/coffeeAgntcy/pull/559).

### Built With

(Versions from `coffeeAGNTCY/coffee_agents/lungo/uv.lock` and `lungo/frontend/package-lock.json`.)

- [AGNTCY App SDK](https://github.com/agntcy/app-sdk) = v0.5.5
- [SLIM](https://github.com/agntcy/slim) = v1.0.0
- [NATS](https://github.com/nats-io/nats-server) = latest
- [A2A](https://github.com/a2aproject/a2a-python) = v0.3.20
- [MCP](https://github.com/modelcontextprotocol/python-sdk) = v1.26.0
- [LangGraph](https://github.com/langchain-ai/langgraph) = v1.0.7
- [Observe SDK](https://github.com/agntcy/observe) = 1.0.41
- [AGNTCY Identity Service SDK](https://github.com/agntcy/identity-service) = 0.0.7
- [AGNTCY Directory](https://github.com/agntcy/dir) = v1.0.0

### Changeset

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/576">#576</a> — @pregnor — docs(README,CHANGELOG): update to 0.1.0 release</summary>

- Published the **0.1.0 — Heartbeat** changelog entry and aligned root **README** “Built With” pins with Lungo lockfiles.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/564">#564</a> — @delthazor — Fix test flakiness by cleaning up leftover transport sockets</summary>

- Closes transport sockets on test teardown (including error paths) so GC does not emit warnings that fail CI.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/571">#571</a> — @delthazor — Fix backend leak by adding DELETE workflow endpoint</summary>

- Adds authenticated **DELETE** for workflow instances; UI calls it when leaving a view.
- Introduces **`WORKFLOW_API_KEY`** / **`VITE_AGENTIC_WORKFLOWS_API_KEY`** wiring across Compose, Helm, and tests.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/369">#369</a> — @JulianLegler — feat(colombia-farm): use weather service mcp results in inventory prompt</summary>

- Feeds weather MCP output into the Colombia farm inventory prompt for weather-aware yield estimates.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/581">#581</a> — @arpad-csepi — refactor: use uv docker base image for agents</summary>

- Agent Dockerfiles use the official **`uv`** image; reported ~30s faster local Compose builds for agent services.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/559">#559</a> — @mihaialexandrescu — feat(lungo, corto): limit release age for pulled uv and npm dependencies</summary>

- **`exclude-newer = "28 days"`** (`uv`) and **`min-release-age=28`** (npm) on Lungo and Corto frontends.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/596">#596</a> — @mihaialexandrescu — feat: Dockerfiles - pin uv and npm cache location and use per-project id field in Buildkit cache</summary>

- Pins **`UV_CACHE_DIR`** / npm cache paths; per-project BuildKit cache IDs (`lungo`, `corto`, `recruiter`).
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/597">#597</a> — @pregnor — feat(lungo,age-wf): add ingress, fix port & local-cluster</summary>

- Dedicated **Ingress** for Agentic Workflows API; NodePort **30083 → 30084**; **`lungo-local-cluster@0.4.0`** with subchart **0.1.1** dependencies and **`payment-mcp-server`**.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/599">#599</a> — @pregnor — fix(lungo,helm): fix SLIM shared secret propagation</summary>

- Chart values can override incomplete ExternalSecrets for **`SLIM_SHARED_SECRET`**.
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/600">#600</a> — @mihaialexandrescu — feat: add .dockerignore at repo root level</summary>

- Root **`.dockerignore`** excludes `.git`, `.venv`, pytest caches, and other build-context noise (Compose uses repo root as context).
</details>

<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/601">#601</a> — @pregnor — release(lungo,helm,ui): bump chart ->0.1.1</summary>

- **`lungo-ui@0.1.1`** and Lungo service subcharts **0.1.1** for workflow API key propagation from #571.
</details>



<details>
<summary><a href="https://github.com/agntcy/coffeeAgntcy/pull/604">#604</a> — @pregnor — release: 0.1.1</summary>

- Bumped **lungo-ui** chart in lungo-local-cluster to **0.1.1** chart version and also lungo-local-cluster to **0.4.1**.
</details>

### Contributors

**First-time contributors** — thank you for your first merged contribution to coffeeAgntcy:

- [@JulianLegler](https://github.com/JulianLegler)
- [@arpad-csepi](https://github.com/arpad-csepi)

---

## 0.1.0 — Heartbeat (2026-05-19)

Milestone release: **live workflow-instance events** on the backend and **dynamic graph animations** in the Lungo UI, plus agentic-workflows APIs, SSE streaming, SLIM-first transport, and A2A card-driven transport selection.

### Summary

**Breaking / migration (read first)**

- **Lungo transport defaults to SLIM** — `DEFAULT_MESSAGE_TRANSPORT` is now `SLIM` (was NATS). Configure **`SLIM_SERVER`**, **`NATS_SERVER`**, and **`SLIM_SHARED_SECRET`** (required; use a random 32+ character value). `TRANSPORT_SERVER_ENDPOINT` remains supported in Compose/Helm for compatibility; prefer the new variables in `.env` (see `.env.example`).
- **Split frontend configuration** — all `VITE_*` variables belong in **`lungo/frontend/.env`** only (copy from `frontend/.env.example`). Do not duplicate them in `lungo/.env`.
- **Docker Compose profiles** — `COMPOSE_PROFILES` includes `frontend` by default. For local Vite dev (`npm run dev`), **omit** `frontend` from `COMPOSE_PROFILES` and run Compose + Vite as described in the [Lungo README](coffeeAGNTCY/coffee_agents/lungo/README.md).
- **CORS** — optional `CORS_ALLOWED_ORIGINS` (comma-separated browser origins). When unset, defaults are `http://localhost:3000` and `http://127.0.0.1:3000`.
- **AGNTCY Directory v1.0.0** — Lungo dev deps pin `agntcy-dir==1.0.0`; refresh local Directory/OASF tooling if you push or query records.
- **Helm chart versions** — Lungo agent/MCP subcharts bump to **0.1.0**; umbrellas **`lungo-local-cluster`** and **`corto-local-cluster`** to **0.2.0**; new **`agentic-workflows-api@0.0.2`**; **`corto-exchange@0.0.8`**. Run `helm dependency update` on umbrella charts before upgrade.
- **Pinned LLM stack (Corto/Recruiter)** — `litellm` and `langchain-litellm` are exact-pinned (see Dependencies).

**Migration steps**

1. From `coffeeAGNTCY/coffee_agents/lungo/`:

    ```sh
    cp .env.example .env
    cp frontend/.env.example frontend/.env
    ```

2. In `lungo/.env`, set transport (minimal SLIM setup):

    ```env
    DEFAULT_MESSAGE_TRANSPORT=SLIM
    SLIM_SERVER="slim:46357"
    NATS_SERVER="nats:4222"
    SLIM_SHARED_SECRET="<random-32plus-chars>"
    ```

   For NATS instead: `DEFAULT_MESSAGE_TRANSPORT=NATS` and ensure NATS is running.

3. In `lungo/frontend/.env`, point the UI at the new API (example):

    ```env
    VITE_AGENTIC_WORKFLOWS_API_URL=http://127.0.0.1:9105
    ```

4. Reconcile `COMPOSE_PROFILES` with how you run the UI (Compose `frontend` profile vs `npm run dev`).
5. Reinstall Python deps: `uv sync` in `lungo/`, `corto/`, and `recruiter/` as needed.
6. If the UI is not on port 3000, set `CORS_ALLOWED_ORIGINS` to your browser origin. Example: `http://localhost:1234`.
7. **Helm / KinD:** upgrade `lungo-local-cluster` to **0.2.0**, run `helm dependency update`, and set per-subchart `config.slimServer`, `config.natsServer`, and `SLIM_SHARED_SECRET` (via `externalSecrets` or `config.slimSharedSecret`). See `lungo/deployment/helm/local-cluster/README.md`.

**Highlights**

- **Workflow instance events** — versioned JSON Schema, in-memory state store, middleware + REST/SSE endpoints, and UI consumption for live progress.
- **Dynamic Lungo graph** — React Flow animations driven by live workflow-instance events.
- **Agentic workflows API** — catalog/sub-API, LHS menu wired to workflows, workflow-context propagation across supervisors.
- **A2A card-driven transport** — multi-transport agent cards; supervisors use `A2AClientFactory` and async iterator messaging.
- **SLIM transport in Compose/Helm** — SLIM-first defaults, shared-secret wiring, and chart bumps for local-cluster installs.
- **Recruiter** — Claude Code plugin for Directory discovery and A2A messaging.
- **Separate UI Docker profile** — optional `frontend` Compose profile and documented local UI workflow.

### Dependencies

| Component | 0.0.77 | 0.1.0 |
| --- | --- | --- |
| [AGNTCY App SDK](https://github.com/agntcy/app-sdk) (Lungo) | 0.4.7 | **0.5.5** |
| [A2A Python SDK](https://github.com/a2aproject/a2a-python) (Lungo) | 0.3.2 | **0.3.20** |
| [AGNTCY Directory](https://github.com/agntcy/dir) (`agntcy-dir`, Lungo dev) | ≥ 0.6.0 | **1.0.0** |
| [Observe SDK](https://github.com/agntcy/observe) (Lungo) | 1.0.34 | **1.0.41** |
| `slim-bindings` / `slima2a` (Lungo) | — | **1.1.0** / **0.3.0** |
| `langchain-litellm` (Lungo, Corto, Recruiter) | ≥ 0.3.0 | **== 0.3.5** |
| `litellm` (Corto, Recruiter) | ≥ 1.82.0 | **== 1.82.1** |
| `axios` (Corto/Lungo frontends) | ^1.13.0 | **1.13.5** |

### Changeset

| ID | Author | Title |
| --- | --- | --- |
| [#492](https://github.com/agntcy/coffeeAgntcy/pull/492) | codyhartsook | hotfix(litellm): pin litellm version in corto and recruter to 1.82.1 |
| [#494](https://github.com/agntcy/coffeeAgntcy/pull/494) | delthazor | (fix) Update incorrect OASF records |
| [#493](https://github.com/agntcy/coffeeAgntcy/pull/493) | codyhartsook | chore: pin langchain-litellm to 0.5.3 |
| [#491](https://github.com/agntcy/coffeeAgntcy/pull/491) | mihaialexandrescu | chore: use tests folder name also under Recruiter |
| [#489](https://github.com/agntcy/coffeeAgntcy/pull/489) | mihaialexandrescu | feat: update pytest integration tests command |
| [#490](https://github.com/agntcy/coffeeAgntcy/pull/490) | delthazor | Update OASF push script |
| [#501](https://github.com/agntcy/coffeeAgntcy/pull/501) | misi-bp | [Docker]: Separate UI profile & add UI local running |
| [#503](https://github.com/agntcy/coffeeAgntcy/pull/503) | pregnor | chore(dep,lungo,recruiter): upgrade dir to v1.0.0 |
| [#504](https://github.com/agntcy/coffeeAgntcy/pull/504) | pregnor | chore(lungo,frontend): sync frontend deps |
| [#502](https://github.com/agntcy/coffeeAgntcy/pull/502) | pregnor | test(recruiter,cache): fix flaky cache hit time |
| [#468](https://github.com/agntcy/coffeeAgntcy/pull/468) | delthazor | Initial approach for state message schema |
| [#498](https://github.com/agntcy/coffeeAgntcy/pull/498) | codyhartsook | Add Claude Code plugin for agent discovery and A2A messaging |
| [#507](https://github.com/agntcy/coffeeAgntcy/pull/507) | pregnor | chore(corto,lungo): pin axios to 1.13.5 |
| [#506](https://github.com/agntcy/coffeeAgntcy/pull/506) | pregnor | chore(recruiter,claude,plugin): fix abs tmp path |
| [#508](https://github.com/agntcy/coffeeAgntcy/pull/508) | pregnor | feat(lungo,schema): gen event schema types |
| [#511](https://github.com/agntcy/coffeeAgntcy/pull/511) | pregnor | feat(lungo,api,workflow): add skeleton |
| [#515](https://github.com/agntcy/coffeeAgntcy/pull/515) | pregnor | fix(api,cors): add cors origins |
| [#521](https://github.com/agntcy/coffeeAgntcy/pull/521) | pregnor | release(helm,APIs): bump CORS helm charts |
| [#517](https://github.com/agntcy/coffeeAgntcy/pull/517) | mihaialexandrescu | feat: add catalog agentic workflows subAPI endpoints |
| [#527](https://github.com/agntcy/coffeeAgntcy/pull/527) | pregnor | fix(lungo,agentic-wf): fix path instance ID |
| [#514](https://github.com/agntcy/coffeeAgntcy/pull/514) | codyhartsook | feat: enable A2A card-driven transport negotiation |
| [#513](https://github.com/agntcy/coffeeAgntcy/pull/513) | delthazor | Initial version for in-memory state storage |
| [#505](https://github.com/agntcy/coffeeAgntcy/pull/505) | delthazor | (fix) Auction test flakiness fix for timeout errors |
| [#526](https://github.com/agntcy/coffeeAgntcy/pull/526) | pregnor | release(lungo,SLIM): update compose,charts with new SLIM transport |
| [#534](https://github.com/agntcy/coffeeAgntcy/pull/534) | pregnor | test(lungo): fix plugin teardown issue |
| [#533](https://github.com/agntcy/coffeeAgntcy/pull/533) | delthazor | Remove workflow minimum requirement |
| [#535](https://github.com/agntcy/coffeeAgntcy/pull/535) | delthazor | Implement SSE endpoints |
| [#538](https://github.com/agntcy/coffeeAgntcy/pull/538) | misi-bp | feat(lungo icons): Replace icons and unify icon usage |
| [#536](https://github.com/agntcy/coffeeAgntcy/pull/536) | mihaialexandrescu | feat(lungo): add Skill for jsonschema to pydanticv2 types |
| [#547](https://github.com/agntcy/coffeeAgntcy/pull/547) | delthazor | Add test env to UI |
| [#539](https://github.com/agntcy/coffeeAgntcy/pull/539) | delthazor | Implement sub-API middleware endpoints for workflow instance states |
| [#548](https://github.com/agntcy/coffeeAgntcy/pull/548) | codyhartsook | feat(lungo): propagate workflow context across supervisors (#453) |
| [#550](https://github.com/agntcy/coffeeAgntcy/pull/550) | pregnor | chore(lungo,env): updated SLIM and NATS serveraddr |
| [#549](https://github.com/agntcy/coffeeAgntcy/pull/549) | mihaialexandrescu | feat(lungo): update left hand side menu to use agentic-workflows api |
| [#528](https://github.com/agntcy/coffeeAgntcy/pull/528) | codyhartsook | feat(lungo): emit workflow-instance state progress via A2A middleware (#453) |
| [#554](https://github.com/agntcy/coffeeAgntcy/pull/554) | mihaialexandrescu | fix(lungo): add scenario field to event stream metadata |
| [#560](https://github.com/agntcy/coffeeAgntcy/pull/560) | pregnor | docs(README): add milestones as planned |
| [#551](https://github.com/agntcy/coffeeAgntcy/pull/551) | delthazor | Implement UI workflow instance event endpoints |
| [#566](https://github.com/agntcy/coffeeAgntcy/pull/566) | misi-bp | fix(heartbreak-release): Icons reset |
| [#570](https://github.com/agntcy/coffeeAgntcy/pull/570) | pregnor | refactor(wf,lhs): patterns, docs, lhs menu (John) |
| [#572](https://github.com/agntcy/coffeeAgntcy/pull/572) | codyhartsook | feat(fe,graph): dynamic animations from live workflow events |
| [#573](https://github.com/agntcy/coffeeAgntcy/pull/573) | isaacc2 | docs(README): corrected grammar |

### Contributors

**First-time contributors** — thank you for your first merged contribution to coffeeAgntcy:

- [@isaacc2](https://github.com/isaacc2)

---

## 0.0.59 (2025-11-24)
## 🚨 Breaking Changes
### 🔧 Migration from `cnoe-agent-utils` to `litellm`
We have replaced the internal LLM provider dependency `cnoe-agent-utils` with `litellm` to enable support for a wider range of LLM providers.

**Impact**
- This is a **breaking change**.
- Environment variables for LLM credentials must be updated in your environment to match the litellm convention for your preferred LLM provider. For a comprehensive list of supported providers, see the [official litellm documentation](https://docs.litellm.ai/docs/providers).
- LLM provider and model must be specified by the LLM_MODEL env variable. Examples:

#### **OpenAI**

```env
LLM_MODEL="openai/<model_of_choice>"
OPENAI_API_KEY=<your_openai_api_key>
```

#### **Azure OpenAI**

```env
LLM_MODEL="azure/<your_deployment_name>"
AZURE_API_BASE=https://your-azure-resource.openai.azure.com/
AZURE_API_KEY=<your_azure_api_key>
AZURE_API_VERSION=<your_azure_api_version>
```

#### **GROQ**

```env
LLM_MODEL="groq/<model_of_choice>"
GROQ_API_KEY=<your_groq_api_key>
```

---

## 0.0.1 (2025-05-30)
### Feat
- **Corto Demo**: Completed the implementation of the Corto demo, including:
  - **Frontend**:
    - Developed a React-based frontend for the Corto Exchange
  - **Backend**:
    - Implemented the Corto Exchange backend with modules for:
      - SLIM transport integration
      - A2A client
      - Graph operations
      - Main entry point
    - Developed the Corto Farm backend with:
      - SLIM transport integration
      - A2A agent execution and card management
      - Farm server
  - **Configuration**:
    - Docker support
    - Example environment file
    - Logging and server configuration
  - **Documentation**:
