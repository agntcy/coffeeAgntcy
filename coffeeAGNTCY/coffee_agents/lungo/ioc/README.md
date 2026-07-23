# IoC (Internet of Cognition) CFN stack

Local Docker Compose setup for the IoC Cognition Fabric Node (CFN) dependencies, integrated
into Lungo. Adapted from the upstream project:
<https://github.com/outshift-open/ioc-cfn-mgmt-backend-svc>

`compose.yaml` is pulled into `lungo/docker-compose.yaml` via the top-level `include:`
directive, so it loads as its own Compose project (this folder is its project directory) and
its services merge into the Lungo model. All services live in a single **`ioc` profile**.

## Run

From `lungo/`:

```bash
COMPOSE_PROFILES=ioc docker compose up      # or add `ioc` to COMPOSE_PROFILES in .env
docker compose --profile ioc up             # equivalent one-off
docker compose --profile ioc down
```

Configuration comes from the **IoC section of `lungo/.env`** (copy `lungo/.env.example`).
Replace every `CHANGE ME` value before using this outside local development.

| Service | Host port | Notes |
|---|---|---|
| `ioc-knowledge-memory-svc-db` | 5456 → 5432 | Postgres + AgensGraph + pgvector; hosts `cfn_mgmt` + `cfn_cp` |
| `ioc-cfn-mgmt-plane-svc` | 9000 | Management plane backend |
| `ioc-cfn-mgmt-plane-ui` | 9001 | Management plane UI |
| `ioc-cfn-svc` | 9002 (HTTP), 9009 → 9001 (MCP) | Cognition Fabric Node |
| `ioc-knowledge-memory-svc` | 9003 | Graph + vector memory |
| `ioc-cfn-cognition-engines` | 9004 | Cognitive services |

> **Ports:** `ioc-cfn-mgmt-plane-svc` uses host `9000`. Lungo's `observability` ClickHouse
> was moved to host `9100` (container port unchanged at `9000`), so `ioc` and `observability`
> can run together.

## Maintenance contract

`compose.yaml` intentionally mirrors the upstream `docker-compose.yml` so upstream changes
map here 1:1. Only **three** deliberate, mechanical deviations are applied:

1. **`IOC_` prefix on every interpolated variable.** Upstream `${FOO}` becomes `${IOC_FOO}`.
   Variables already prefixed upstream (`IOC_KNOWLEDGE_DB*`) are left as-is — never
   double-prefixed. **Container-side names (the `LLM_MODEL=` left-hand side) and all `:-`
   defaults are kept exactly as upstream.** The prefix namespaces these vars so they can live
   in Lungo's shared `.env` without colliding with — or leaking into — Lungo's own services
   (which load `.env` via `env_file`).
2. **`build:` blocks dropped** — no IoC source in this repo, so we use the published images only.
3. **Single `ioc` profile** (per issue #700) instead of upstream's `full-stack` /
   `mgmt-plane` / `data-plane` profiles.

### Env-file translation rule (`.env` / `.env.example`)

The IoC section of `lungo/.env` and `lungo/.env.example` mirrors the upstream **`.env.example`**
(same section grouping and order) under one translation rule:

- **Prefix every variable with `IOC_`** (names already prefixed upstream, `IOC_KNOWLEDGE_DB*`,
  are kept as-is — never double-prefixed).
- **Keep a var active (uncommented) only if `compose.yaml` actually interpolates it.** Every
  other upstream var is carried as a **commented `# not consumed: <reason>` entry** so the file
  stays a faithful, diffable mirror without changing runtime behavior. A var is "not consumed"
  when it is hardcoded in `compose.yaml` (e.g. `POSTGRES_DB`, `MCP_PORT`), only applies to
  running a service outside Docker (e.g. `POSTGRES_PORT`, `POSTGRES_HOST_PORT`), or is an
  app-internal knob compose never passes (e.g. `DB_ECHO`, `DB_SSL_MODE`, `DEFAULT_PAGE_SIZE`).

The mirror also works in reverse: a var that upstream references only in `docker-compose.yml`
(not their `.env.example`) is still carried here — see the `IOC_LLM_PROVIDER` note below.

### To re-sync with upstream

1. Diff upstream `docker-compose.yml` against this file (ignoring the three deviations above).
2. Apply each change here, prefixing any new `${VAR}` interpolation with `IOC_`.
3. Diff upstream `.env.example` against the IoC section of `lungo/.env(.example)` and apply the
   **env-file translation rule** above: prefix with `IOC_`, keep active only what `compose.yaml`
   interpolates, and carry the rest as commented `# not consumed` entries. Keep `.env` and
   `.env.example` in lockstep.
4. Validate: `cd lungo && docker compose --profile ioc config -q`.

### Note on `IOC_LLM_PROVIDER`

`IOC_LLM_PROVIDER` maps to upstream's `LLM_PROVIDER`, which the upstream **`docker-compose.yml`**
references on `ioc-cfn-svc` as `${LLM_PROVIDER:-azure-openai}`. It is *not* listed in the
upstream `.env.example` (their example omits it because it has a default), but it is a real
compose variable, so we carry it as a documented knob. Because it defaults to `azure-openai`,
it is optional.

## Files

- `compose.yaml` — the IoC services (`ioc` profile).
- `scripts/init-multi-db.sh` — creates the `cfn_mgmt` and `cfn_cp` databases on first DB init.
- `.secrets/` — bind-mounted read-only into `ioc-cfn-mgmt-plane-svc`. Keep empty (a `.gitkeep`
  holds the path); do not commit real secrets here. The management service can instead take a
  `MEMORY_PROVIDER_ENCRYPTION_KEY` env var.
