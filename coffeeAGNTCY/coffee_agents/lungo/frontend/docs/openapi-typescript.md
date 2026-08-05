# OpenAPI → TypeScript types (Lungo frontend)

Generated types for the **Agentic Workflows API** keep the UI aligned with `coffeeAGNTCY/coffee_agents/lungo/schema/openapi/` and the linked `event_v1` JSON Schema.

## Generated output

| Artifact | Source |
|----------|--------|
| `src/api/generated/agenticWorkflows.openapi.ts` | `../schema/openapi/openapi.yaml` |
| `src/api/agenticWorkflowsTypes.ts` | Thin aliases + small UI/runtime extensions (e.g. node `position`) |

Do **not** edit `agenticWorkflows.openapi.ts` by hand.

## Regenerate locally

From `coffeeAGNTCY/coffee_agents/lungo/frontend`:

```bash
npm run generate:api-types
```

Commit the updated `src/api/generated/agenticWorkflows.openapi.ts` with any OpenAPI or JSON Schema change.

## CI drift check

```bash
npm run check:api-types
```

Regenerates types and fails if the committed file differs (`git diff --exit-code`). FE CI runs this step when frontend or OpenAPI/schema paths change.

## Backend parity

When OpenAPI or `schema/jsonschemas/event_v1.json` changes, regenerate Python routers/types per the lungo **openapi-to-python-lungo** skill, then run `npm run generate:api-types` here.

## Tooling

- [openapi-typescript](https://github.com/openapi-ts/openapi-typescript) v7 (devDependency)
- Existing HTTP clients (`fetchJson`, `agenticWorkflowsClient`) stay hand-written; only types are generated.

## UI catalog types

`WorkflowSummary` in `src/utils/agenticWorkflowsApi.ts` remains the **normalized** shape used in the sidebar and chat routing. `GET /agentic-workflows/` is typed as `WorkflowSummaryMapResponse`; `parseWorkflowSummaryRow` tolerates legacy rows missing capability fields before normalization.
