/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import type { Pattern } from "@/utils/patternLibraryApi"
import {
  REFERENCE_LIBRARY_KEY,
  addNewlyAvailableExpandedKeys,
  buildCatalogSidebarLayout,
  buildInitialExpanded,
  makePatternKey,
  makeReferenceCategoryKey,
} from "./sidebar.utils"

const workflow: WorkflowSummary = {
  name: "Publish Subscribe",
  pattern: "Supervisor",
  pattern_category: "Orchestration & Control Flow",
  use_case: "Coffee Agntcy",
  scenario: "Purchasing",
  supports_sse: false,
  supports_streaming: false,
  chat_api_target: "exchange",
}

const patterns: Pattern[] = [
  {
    name: "Feedback Loop",
    pattern_category: "Learning, Feedback & Self-Improvement",
    implemented: false,
  },
  {
    name: "Supervisor",
    pattern_category: "Orchestration & Control Flow",
    implemented: true,
  },
]

describe("buildCatalogSidebarLayout", () => {
  it("builds workflows and the full reference library from independent inputs", () => {
    const layout = buildCatalogSidebarLayout([workflow], patterns, [
      "Orchestration & Control Flow",
      "Learning, Feedback & Self-Improvement",
    ])

    expect(layout.implementedPatterns.map((pattern) => pattern.name)).toEqual([
      "Supervisor",
    ])
    expect(layout.referenceCategories).toEqual([
      {
        name: "Orchestration & Control Flow",
        patternNames: ["Supervisor"],
      },
      {
        name: "Learning, Feedback & Self-Improvement",
        patternNames: ["Feedback Loop"],
      },
    ])
  })
})

describe("addNewlyAvailableExpandedKeys", () => {
  it("adds keys from the second response without reopening a user-collapsed key", () => {
    const workflowLayout = buildCatalogSidebarLayout([workflow])
    const workflowDefaults = buildInitialExpanded(workflowLayout)
    const collapsed = new Set(workflowDefaults)
    collapsed.delete(makePatternKey("Supervisor"))

    const completeLayout = buildCatalogSidebarLayout([workflow], patterns)
    const completeDefaults = buildInitialExpanded(completeLayout)
    const merged = addNewlyAvailableExpandedKeys(
      collapsed,
      workflowDefaults,
      completeDefaults,
    )

    expect(merged.has(makePatternKey("Supervisor"))).toBe(false)
    expect(merged.has(REFERENCE_LIBRARY_KEY)).toBe(true)
    expect(
      merged.has(makeReferenceCategoryKey("Orchestration & Control Flow")),
    ).toBe(true)
  })
})
