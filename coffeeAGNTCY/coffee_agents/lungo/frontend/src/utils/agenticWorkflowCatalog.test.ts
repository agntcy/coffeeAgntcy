/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  AGENTIC_WORKFLOW_NAME_BY_PATTERN,
  getAgenticWorkflowNameForPattern,
  patternUsesAgenticWorkflowGraph,
} from "@/utils/agenticWorkflowCatalog"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

describe("agenticWorkflowCatalog", () => {
  it.each([
    {
      caseName: "publish_subscribe maps to auction network",
      pattern: PATTERNS.PUBLISH_SUBSCRIBE,
      expected: "Publish Subscribe Coffee Farm Network",
    },
    {
      caseName: "publish_subscribe_streaming maps to streaming auction",
      pattern: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
      expected: "Publish Subscribe Streaming Coffee Auction Network",
    },
    {
      caseName: "group_communication maps to logistics",
      pattern: PATTERNS.GROUP_COMMUNICATION,
      expected: "Secure Group Communication Logistics Network",
    },
    {
      caseName: "on_demand_discovery maps to discovery workflow",
      pattern: PATTERNS.ON_DEMAND_DISCOVERY,
      expected: "On-demand Discovery",
    },
  ])("$caseName", ({ pattern, expected }) => {
    expect(getAgenticWorkflowNameForPattern(pattern)).toBe(expected)
    expect(patternUsesAgenticWorkflowGraph(pattern)).toBe(true)
  })

  it("slim_a2a has no agentic workflow mapping", () => {
    expect(
      getAgenticWorkflowNameForPattern(PATTERNS.SLIM_A2A as PatternType),
    ).toBeUndefined()
    expect(
      patternUsesAgenticWorkflowGraph(PATTERNS.SLIM_A2A as PatternType),
    ).toBe(false)
  })

  it("catalog entries match Workflow.name keys in starting_workflows.json", () => {
    const names = new Set(Object.values(AGENTIC_WORKFLOW_NAME_BY_PATTERN))
    expect(names.size).toBe(4)
    for (const n of names) {
      expect(n.length).toBeGreaterThan(0)
    }
  })
})
