/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Minimal TypeScript shapes for Agentic Workflows API + event_v1 payloads.
 **/

export interface TopologySize {
  width?: number
  height?: number
}

export interface TopologyPosition {
  x: number
  y: number
}

export interface TopologyNodeWire {
  id: string
  operation?: string
  type?: string
  label?: string
  size?: TopologySize
  layer_index?: number
  /** Optional absolute layout hint; when present the renderer skips auto-layout for this node. */
  position?: TopologyPosition
  agent_record_uri?: string
  stable_agent_id?: string | { root: string }
  /** Backend OASF enrichment (see api/agentic_workflows/agent_ui_enrichment.py). */
  agent_directory_cid?: string
  identity_app_slug?: string
  has_badge_override?: boolean
  has_policy_override?: boolean
  verification_status_override?: "verified" | "failed"
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

export interface WorkflowInstanceWire {
  id: string
  topology?: TopologyWire
  [key: string]: unknown
}

export interface EventV1Wire {
  metadata?: {
    id?: string
    type?: string
    [key: string]: unknown
  }
  data?: {
    workflows?: Record<
      string,
      {
        instances?: Record<string, WorkflowInstanceWire>
        [key: string]: unknown
      }
    >
    [key: string]: unknown
  }
}

export interface InstantiateWorkflowResponseWire {
  workflow_instance_id: string
}
