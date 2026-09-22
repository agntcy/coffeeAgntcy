/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  buildCatalogSidebarLayout,
  buildInitialExpanded,
  makePatternKey,
  makeReferenceCategoryKey,
} from "./sidebar.utils"

const ORCHESTRATION = "Orchestration & Control Flow"
const LEARNING = "Learning, Feedback & Self-Improvement"

const makeSummary = (over: Partial<WorkflowSummary>): WorkflowSummary => ({
  name: "Workflow",
  pattern: "Supervisor",
  pattern_category: ORCHESTRATION,
  use_case: "Coffee Agntcy",
  scenario: "Purchasing",
  supports_sse: false,
  supports_streaming: false,
  chat_api_target: "exchange",
  ...over,
})

/** Reference Library row as it appears in the catalog: name === pattern, "---" markers. */
const makeReferenceRow = (name: string, category: string): WorkflowSummary =>
  makeSummary({
    name,
    pattern: name,
    pattern_category: category,
    use_case: "---",
    scenario: "---",
    chat_api_target: null,
  })

describe("buildCatalogSidebarLayout", () => {
  /** "Supervisor" is both an implemented pattern and a Reference Library entry. */
  const summaries: WorkflowSummary[] = [
    makeSummary({ name: "Publish Subscribe" }),
    makeReferenceRow("Feedback Loop", LEARNING),
    makeReferenceRow("Supervisor", ORCHESTRATION),
  ]

  it("keeps the reference row of an implemented pattern out of the implemented tree", () => {
    const { implementedPatterns } = buildCatalogSidebarLayout(summaries)

    expect(implementedPatterns.map((pattern) => pattern.name)).toEqual([
      "Supervisor",
    ])
    expect(
      implementedPatterns[0].useCaseScenarios.flatMap((ucs) =>
        ucs.workflows.map((workflow) => workflow.summary.name),
      ),
    ).toEqual(["Publish Subscribe"])
  })

  it("lists an implemented pattern in the Reference Library under its category", () => {
    const { referenceCategories } = buildCatalogSidebarLayout(summaries, [
      ORCHESTRATION,
      LEARNING,
    ])

    expect(referenceCategories).toEqual([
      { name: ORCHESTRATION, patternNames: ["Supervisor"] },
      { name: LEARNING, patternNames: ["Feedback Loop"] },
    ])
  })

  it("expands both sections of a dual-listed pattern without key collisions", () => {
    const layout = buildCatalogSidebarLayout(summaries)
    const expanded = buildInitialExpanded(layout)

    expect(expanded.has(makePatternKey("Supervisor"))).toBe(true)
    expect(expanded.has(makeReferenceCategoryKey(ORCHESTRATION))).toBe(true)
    // Reference entries are leaves, so the bare pattern name is never an expand key.
    expect(expanded.has("Supervisor")).toBe(false)
  })
})
