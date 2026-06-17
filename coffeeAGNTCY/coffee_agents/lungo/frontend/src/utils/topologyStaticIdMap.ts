/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * TEMPORARY: Wire-id → static NODE_ID map for patterns with a hand-tuned graph.
 *
 * Bridges dynamic wire ids (stable_agent_id, transport canonical key, label)
 * to the NODE_IDS authored in `graphConfigs.ts` / `graphConfigsData.tsx`, so
 * SSE-driven highlights/animations land on the statically-rendered nodes and
 * edges.
 *
 * Longer term, the four patterns shipped with static configs should render
 * directly from the Agentic Workflows API topology (positions, labels, icons
 * all wire-supplied). At that point the wire id == the rendered id, this
 * module is no longer needed, and `graphConfigs.ts` / `graphConfigsData.tsx`
 * can be removed or reduced to animation sequences only.
 * -----------------------------------------------------------------------------
 */

import { stableAgentUuidForRecordName } from "@/utils/agenticTopologyIdentityUiMap"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

export interface StaticIdMap {
  /** UUID (no `agent://` prefix) -> static NODE_IDS value. */
  idByStableAgentUuid: ReadonlyMap<string, string>
  /** Lowercased wire `label` -> static NODE_IDS value (no stable_agent_id only). */
  idByLabel: ReadonlyMap<string, string>
  /** Transport canonical key (e.g. `"transport"`) -> static NODE_IDS value. */
  idByTransportKey: ReadonlyMap<string, string>
}

function lc(s: string): string {
  return s.trim().toLowerCase()
}

/** Build the P/S id map (also serves PUBLISH_SUBSCRIBE_STREAMING). */
function buildPublishSubscribeIdMap(): StaticIdMap {
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
    [lc("Weather MCP Server"), "6"],
    [lc("Payment MCP Server"), "7"],
  ])
  const idByTransportKey = new Map<string, string>([["transport", "2"]])
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
  }
}

function buildGroupCommunicationIdMap(): StaticIdMap {
  const idByStableAgentUuid = new Map<string, string>([
    [stableAgentUuidForRecordName("Logistics Supervisor agent"), "1"],
    [stableAgentUuidForRecordName("Tatooine Farm agent"), "3"],
    [stableAgentUuidForRecordName("Shipping agent"), "4"],
    [stableAgentUuidForRecordName("Accountant agent"), "5"],
  ])
  const idByLabel = new Map<string, string>([
    [lc("Buyer Logistics Agent"), "1"],
    [lc("Shipper Agent"), "4"],
    [lc("Accountant Agent"), "5"],
    // The group container has no stable_agent_id; match by label only.
    [lc("Logistics Group"), "logistics-group"],
  ])
  const idByTransportKey = new Map<string, string>([["transport", "2"]])
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
  }
}

function buildDiscoveryIdMap(): StaticIdMap {
  // Recruiter middleware may emit the OASF record name or the A2A service
  // card name; both collapse to the static recruiter node.
  const idByStableAgentUuid = new Map<string, string>([
    [
      stableAgentUuidForRecordName("Agentic Recruiter agent"),
      "recruiter-agent",
    ],
    [stableAgentUuidForRecordName("RecruiterAgent"), "recruiter-agent"],
  ])
  const idByLabel = new Map<string, string>([
    [lc("Agentic Recruiter"), "recruiter-agent"],
    // No OASF record for the directory; resolved by label only.
    [lc("AGNTCY Agent Directory"), "agntcy-directory"],
  ])
  // Discovery pattern has no transport node in the static config.
  const idByTransportKey = new Map<string, string>()
  return {
    idByStableAgentUuid,
    idByLabel,
    idByTransportKey,
  }
}

/**
 * Return an id map for the given pattern, or null when the dynamic
 * grid-based layout should be used as-is (no static config to honour).
 */
export function staticIdMapForPattern(
  pattern: PatternType,
): StaticIdMap | null {
  switch (pattern) {
    case PATTERNS.PUBLISH_SUBSCRIBE:
    case PATTERNS.PUBLISH_SUBSCRIBE_STREAMING:
      return buildPublishSubscribeIdMap()
    case PATTERNS.GROUP_MESSAGING:
      return buildGroupCommunicationIdMap()
    case PATTERNS.A2A_HTTP:
      return buildDiscoveryIdMap()
    default:
      return null
  }
}
