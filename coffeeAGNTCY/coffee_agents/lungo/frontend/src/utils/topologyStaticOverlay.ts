/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * Static graph overlay for `topologyWireToReactFlow`.
 *
 * Patterns shipped with hand-tuned positions in `graphConfigsData.tsx`
 * (PUBLISH_SUBSCRIBE, GROUP_COMMUNICATION, ON_DEMAND_DISCOVERY) must keep
 * those positions even when SSE-driven workflow topology is applied. This
 * module supplies a per-pattern translation layer mapping dynamic ids
 * (stable_agent_id, transport canonical id, label) -> the static
 * NODE_IDS used by the React Flow nodes in `graphConfigsData.tsx`.
 *
 * When an overlay is provided to `topologyWireToReactFlow`, that function
 * emits nodes whose ids/positions match the static config, so SSE-driven
 * highlights/animations naturally land on the same nodes/edges the static
 * config laid out.
 * -----------------------------------------------------------------------------
 */

import {
  PUBLISH_SUBSCRIBE_CONFIG,
  GROUP_COMMUNICATION_CONFIG,
  DISCOVERY_CONFIG,
  type GraphConfig,
} from "@/utils/graphConfigsData"
import { stableAgentUuidForRecordName } from "@/utils/agenticTopologyIdentityUiMap"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

export interface StaticOverlay {
  /** UUID (no `agent://` prefix) -> static NODE_IDS value. */
  idByStableAgentUuid: ReadonlyMap<string, string>
  /** Lowercased label/label1/label1+label2 -> static NODE_IDS value. */
  idByLabel: ReadonlyMap<string, string>
  /** Transport canonical key (e.g. `"transport"`) -> static NODE_IDS value. */
  idByTransportKey: ReadonlyMap<string, string>
  /** Static node id -> hand-tuned `{x, y}` from graphConfigsData. */
  positionByStaticId: ReadonlyMap<string, { x: number; y: number }>
}

/** Collect `{id -> position}` for every node in a static GraphConfig. */
function positionsFromConfig(
  config: GraphConfig,
): Map<string, { x: number; y: number }> {
  const out = new Map<string, { x: number; y: number }>()
  for (const node of config.nodes) {
    if (
      node.position &&
      typeof node.position.x === "number" &&
      typeof node.position.y === "number"
    ) {
      out.set(node.id, { x: node.position.x, y: node.position.y })
    }
  }
  return out
}

function lc(s: string): string {
  return s.trim().toLowerCase()
}

/** Build the P/S overlay (also serves PUBLISH_SUBSCRIBE_STREAMING). */
function buildPublishSubscribeOverlay(): StaticOverlay {
  // OASF agent record top-level names; stable_agent_id derives from these via
  // `stableAgentUuidForRecordName`. Must stay in sync with the OASF JSON files
  // under `agents/supervisors/*/oasf/agents/*.json` and the backend in
  // `api/agentic_workflows/workflows.py`.
  const idByStableAgentUuid = new Map<string, string>([
    [stableAgentUuidForRecordName("Auction Supervisor agent"), "1"],
    [stableAgentUuidForRecordName("Brazil Coffee Farm"), "3"],
    [stableAgentUuidForRecordName("Colombia Coffee Farm"), "4"],
    [stableAgentUuidForRecordName("Vietnam Coffee Farm"), "5"],
    [stableAgentUuidForRecordName("Weather MCP Server"), "6"],
    [stableAgentUuidForRecordName("Payment MCP Server"), "7"],
  ])
  const idByLabel = new Map<string, string>([
    // Defensive label fallbacks if the wire lacks a stable_agent_id.
    [lc("Auction Agent"), "1"],
    [lc("Auction Agent Buyer"), "1"],
    [lc("Brazil"), "3"],
    [lc("Colombia"), "4"],
    [lc("Vietnam"), "5"],
    [lc("Weather"), "6"],
    [lc("MCP Server Weather"), "6"],
    [lc("Payment"), "7"],
    [lc("MCP Server Payment"), "7"],
  ])
  const idByTransportKey = new Map<string, string>([["transport", "2"]])
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
    positionByStaticId: positionsFromConfig(PUBLISH_SUBSCRIBE_CONFIG),
  }
}

function buildGroupCommunicationOverlay(): StaticOverlay {
  const idByStableAgentUuid = new Map<string, string>([
    [stableAgentUuidForRecordName("Logistics Supervisor agent"), "1"],
    [stableAgentUuidForRecordName("Tatooine Farm agent"), "3"],
    [stableAgentUuidForRecordName("Shipping agent"), "4"],
    [stableAgentUuidForRecordName("Accountant agent"), "5"],
  ])
  const idByLabel = new Map<string, string>([
    [lc("Buyer Logistics Agent"), "1"],
    [lc("Buyer"), "1"],
    [lc("Tatooine"), "3"],
    [lc("Shipper"), "4"],
    [lc("Shipper Agent"), "4"],
    [lc("Accountant"), "5"],
    [lc("Accountant Agent"), "5"],
    // The group container has no stable_agent_id; match by label only.
    [lc("Logistics Group"), "logistics-group"],
  ])
  const idByTransportKey = new Map<string, string>([["transport", "2"]])
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
    positionByStaticId: positionsFromConfig(GROUP_COMMUNICATION_CONFIG),
  }
}

function buildDiscoveryOverlay(): StaticOverlay {
  // Recruiter middleware may emit the OASF record name or the A2A service
  // card name; both collapse to the static recruiter node.
  const idByStableAgentUuid = new Map<string, string>([
    [stableAgentUuidForRecordName("Agentic Recruiter agent"), "recruiter-agent"],
    [stableAgentUuidForRecordName("RecruiterAgent"), "recruiter-agent"],
  ])
  const idByLabel = new Map<string, string>([
    [lc("Agentic Recruiter"), "recruiter-agent"],
    [lc("Agentic Recruiter Discovery and delegation"), "recruiter-agent"],
    [lc("Recruiter"), "recruiter-agent"],
    // No OASF record for the directory; resolved by label only.
    [lc("Directory"), "agntcy-directory"],
    [lc("AGNTCY Agent Directory"), "agntcy-directory"],
    [lc("Directory AGNTCY Agent Directory"), "agntcy-directory"],
  ])
  // Discovery pattern has no transport node in the static config.
  const idByTransportKey = new Map<string, string>()
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
    positionByStaticId: positionsFromConfig(DISCOVERY_CONFIG),
  }
}

/**
 * Return an overlay for the given pattern, or null when the dynamic
 * grid-based layout should be used as-is (no static config to honour).
 */
export function overlayForPattern(
  pattern: PatternType,
): StaticOverlay | null {
  switch (pattern) {
    case PATTERNS.PUBLISH_SUBSCRIBE:
    case PATTERNS.PUBLISH_SUBSCRIBE_STREAMING:
      return buildPublishSubscribeOverlay()
    case PATTERNS.GROUP_COMMUNICATION:
      return buildGroupCommunicationOverlay()
    case PATTERNS.ON_DEMAND_DISCOVERY:
      return buildDiscoveryOverlay()
    default:
      return null
  }
}
