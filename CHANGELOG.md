# Changelog

## 0.1.0 — Heartbeat (2026-05-19)

Milestone release: **live workflow-instance events** on the backend and **dynamic graph animations** in the Lungo UI, plus agentic-workflows APIs, SSE streaming, and A2A card-driven transport selection.

### Summary

**Breaking / migration (read first)**

- **Lungo transport defaults to SLIM** — `DEFAULT_MESSAGE_TRANSPORT=SLIM` replaces NATS-as-default. `TRANSPORT_SERVER_ENDPOINT` is removed in favor of `SLIM_SERVER`, `NATS_SERVER`, and **`SLIM_SHARED_SECRET`** (required; use a random 32+ character value).
- **Split frontend configuration** — all `VITE_*` variables belong in **`lungo/frontend/.env`** only (copy from `frontend/.env.example`). Do not duplicate them in `lungo/.env`.
- **Docker Compose profiles** — `COMPOSE_PROFILES` now includes `frontend` by default. For local Vite dev (`npm run dev`), **omit** `frontend` from `COMPOSE_PROFILES` and run Compose + Vite as described in the [Lungo README](coffeeAGNTCY/coffee_agents/lungo/README.md).
- **CORS** — optional `CORS_ALLOWED_ORIGINS` (comma-separated UI origins). When unset, defaults are `http://localhost:3000` and `http://127.0.0.1:3000`.
- **AGNTCY Directory v1.0.0** — Lungo dev deps pin `agntcy-dir==1.0.0`; refresh local Directory/OASF tooling if you push or query records.
- **Pinned LLM stack** — `litellm` and `langchain-litellm` are exact-pinned in Corto and Recruiter (see Dependencies).

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

3. Reconcile `COMPOSE_PROFILES` with how you run the UI (Compose `frontend` profile vs `npm run dev`).
4. Reinstall Python deps: `uv sync` in `lungo/`, `corto/`, and `recruiter/` as needed.
5. If the UI is not on port 3000, set `CORS_ALLOWED_ORIGINS` to your browser origin.

**Highlights**

- **Workflow instance events** — versioned JSON Schema, in-memory state store, middleware + REST/SSE endpoints, and UI consumption for live progress.
- **Dynamic Lungo graph** — React Flow animations driven by live workflow-instance events.
- **Agentic workflows API** — catalog/sub-API, LHS menu wired to workflows, workflow-context propagation across supervisors.
- **A2A card-driven transport** — multi-transport agent cards; supervisors use `A2AClientFactory` and async iterator messaging.
- **SLIM transport in Compose/Helm** — updated charts and compose for current SLIM server layout.
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
