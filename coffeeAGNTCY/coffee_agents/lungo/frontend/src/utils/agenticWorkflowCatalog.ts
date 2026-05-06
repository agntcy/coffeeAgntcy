/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Maps Lungo UI pattern slugs to Agentic Workflows catalog keys (`Workflow.name`).
 * Must stay aligned with `api/agentic_workflows/starting_workflows.json`.
 * Epic #540 may replace this with catalog-driven LHS selection; keep a single module.
 **/

import { PATTERNS, type PatternType } from "@/utils/patternUtils"

/** Catalog `name` field / URL path segment for each demo pattern. */
export const AGENTIC_WORKFLOW_NAME_BY_PATTERN: Partial<
  Record<PatternType, string>
> = {
  [PATTERNS.PUBLISH_SUBSCRIBE]: "Publish Subscribe Coffee Farm Network",
  [PATTERNS.PUBLISH_SUBSCRIBE_STREAMING]:
    "Publish Subscribe Streaming Coffee Auction Network",
  [PATTERNS.GROUP_COMMUNICATION]:
    "Secure Group Communication Logistics Network",
  [PATTERNS.ON_DEMAND_DISCOVERY]: "On-demand Discovery",
}

export function getAgenticWorkflowNameForPattern(
  pattern: PatternType,
): string | undefined {
  return AGENTIC_WORKFLOW_NAME_BY_PATTERN[pattern]
}

export function patternUsesAgenticWorkflowGraph(pattern: PatternType): boolean {
  return getAgenticWorkflowNameForPattern(pattern) !== undefined
}
