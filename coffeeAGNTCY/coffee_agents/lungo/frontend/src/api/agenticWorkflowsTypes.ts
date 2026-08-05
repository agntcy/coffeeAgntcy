/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Agentic Workflows API types from OpenAPI (`schema/openapi/openapi.yaml`).
 * Regenerate: `npm run generate:api-types` in `frontend/`.
 * See `docs/openapi-typescript.md`.
 **/

import type { components } from "@/api/generated/agenticWorkflows.openapi"

type Schemas = components["schemas"]

/** OpenAPI component schemas (generated). */
export type AgenticWorkflowsSchemas = Schemas

export type WorkflowSummarySchema = Schemas["WorkflowSummary"]
export type WorkflowSummaryMapResponse = Schemas["WorkflowSummaryMapResponse"]
export type InstantiateWorkflowResponseWire =
  Schemas["InstantiateWorkflowResponse"]
export type WorkflowDocumentationResponse =
  Schemas["WorkflowDocumentationResponse"]

export type TopologySize = Schemas["size"]

/** Layout hint applied by the UI; not part of the canonical event_v1 schema. */
export type TopologyPosition = {
  x: number
  y: number
}

/**
 * Topology node at runtime (SSE / instance JSON). Aligns with event_v1 partial/full
 * nodes but stays permissive: updates often omit `operation` / `layer_index`.
 */
export interface TopologyNodeWire {
  id: string
  operation?: string
  type?: string
  label?: string
  label_subtitle?: string
  size?: TopologySize
  layer_index?: number
  position?: TopologyPosition
  agent_record_uri?: string
  stable_agent_id?: string | { root: string }
  oasf_record?: Record<string, unknown>
  agent_cid?: string
  agent_directory_cid?: string
  identity_app_slug?: string
  has_badge_override?: boolean
  has_policy_override?: boolean
  verification_status_override?: "verified" | "failed"
  message_transport?: string
  [key: string]: unknown
}

export interface TopologyEdgeWire {
  id: string
  operation?: string
  type?: string
  source?: string
  target?: string
  bidirectional?: boolean
  weight?: number
  [key: string]: unknown
}

export interface TopologyWire {
  nodes?: TopologyNodeWire[]
  edges?: TopologyEdgeWire[]
}

export type WorkflowInstanceWire = Schemas["workflow_instance"]

/** SSE / internal event payloads (`event_v1` JSON Schema). */
export type EventV1Wire = Schemas["event_v1"]
