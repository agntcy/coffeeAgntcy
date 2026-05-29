# Changelog

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
