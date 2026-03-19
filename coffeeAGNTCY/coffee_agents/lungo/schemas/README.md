# Session state progress schema

This folder holds the **session state progress** message contract used for backend live state, SSE (NDJSON stream), and A2A state middleware when implemented.

## Message shape

A single message type with discriminator `kind`:

- **`snapshot`** — full state and optional topology (current session view).
- **`event`** — a single event with optional `payload` and `topology_delta`.

Required envelope on every message: `session_id`, `kind`, `timestamp`.

## Schema files

[schemafiles/session_state_progress_v1.json](schemafiles/session_state_progress_v1.json) — JSON Schema (draft 2020-12). Use for validation and tooling. The schema `$id` includes the version path for stable reference.

## Examples

Minimal valid payloads:

- [examples/snapshot_example.json](examples/snapshot_example.json)
- [examples/event_example.json](examples/event_example.json)

## Validation

Python: `schemas.validate.validate_session_state_progress(payload)` (requires `jsonschema`).

CLI: `python -m schemas.schemascripts.validate` — validates all JSON schemas in `schemafiles/`.

## Versioning

The schema is versioned: v1 in the filename and `$id`. Future versions will be added as separate files (e.g. `session_state_progress_v2.json`) without replacing v1.
