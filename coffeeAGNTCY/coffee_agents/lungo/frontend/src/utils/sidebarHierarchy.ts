/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Helpers to turn a flat list of catalog `WorkflowSummary` rows into the
 * LHS sidebar: pattern -> conversation (scenario) -> workflow [-> A2A SLIM], plus
 * a flat Reference Library of placeholder (unimplemented) pattern names.
 */

import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"

/** Label for the transport row under SLIM-backed workflows. */
export const A2A_SLIM_MENU_LABEL = "A2A SLIM"

/** Catalog workflow names that use a workflow header + A2A SLIM child row. */
export const WORKFLOWS_WITH_A2A_SLIM_TRANSPORT_LAYER: ReadonlySet<string> =
  new Set([
    "Publish Subscribe",
    "Publish Subscribe Streaming",
    "Group Messaging",
  ])

export type WorkflowMenuDisplay = "direct" | "slim_transport"

export interface WorkflowNode {
  summary: WorkflowSummary
  display: WorkflowMenuDisplay
}

export interface UseCaseScenarioNode {
  useCase: string
  scenario: string
  /** Middle row label, e.g. "Conversation: Purchasing". */
  label: string
  workflows: WorkflowNode[]
}

export interface PatternNode {
  name: string
  useCaseScenarios: UseCaseScenarioNode[]
}

/** Placeholder catalog rows (pattern docs only; no runnable Lungo workflow). */
export const isPlaceholderWorkflow = (summary: WorkflowSummary): boolean =>
  summary.use_case === "---" && summary.scenario === "---"

export interface CatalogSidebarLayout {
  implementedPatterns: PatternNode[]
  /** Unique pattern names for Reference Library, catalog order. */
  referencePatternNames: string[]
}

export const usesSlimTransportLayer = (workflowName: string): boolean =>
  WORKFLOWS_WITH_A2A_SLIM_TRANSPORT_LAYER.has(workflowName)

const workflowDisplay = (summary: WorkflowSummary): WorkflowMenuDisplay =>
  usesSlimTransportLayer(summary.name) ? "slim_transport" : "direct"

/** Middle-row label: scenario only (use-case is not shown). */
export const formatConversationLabel = (scenario: string): string =>
  `Conversation: ${scenario}`

/** Composite key used to group workflows that share both use-case and scenario. */
const makeUseCaseScenarioGroupKey = (
  useCase: string,
  scenario: string,
): string => `${useCase}|${scenario}`

interface UseCaseScenarioBucket {
  useCase: string
  scenario: string
  workflows: WorkflowNode[]
}

const catalogIndexByName = (
  summaries: readonly WorkflowSummary[],
): Map<string, number> => {
  const m = new Map<string, number>()
  summaries.forEach((s, i) => {
    if (!m.has(s.name)) {
      m.set(s.name, i)
    }
  })
  return m
}

const minIndexForWorkflows = (
  workflows: readonly WorkflowNode[],
  order: Map<string, number>,
): number => {
  let m = Number.POSITIVE_INFINITY
  for (const w of workflows) {
    const idx = order.get(w.summary.name)
    if (idx !== undefined && idx < m) {
      m = idx
    }
  }
  return m
}

const minIndexForPattern = (
  scenarioMap: Map<string, UseCaseScenarioBucket>,
  order: Map<string, number>,
): number => {
  let m = Number.POSITIVE_INFINITY
  for (const bucket of scenarioMap.values()) {
    const b = minIndexForWorkflows(bucket.workflows, order)
    if (b < m) {
      m = b
    }
  }
  return m
}

const groupImplementedSummaries = (
  summaries: readonly WorkflowSummary[],
): PatternNode[] => {
  const order = catalogIndexByName(summaries)
  const byPattern = new Map<string, Map<string, UseCaseScenarioBucket>>()

  for (const summary of summaries) {
    let scenarioMap = byPattern.get(summary.pattern)
    if (scenarioMap === undefined) {
      scenarioMap = new Map<string, UseCaseScenarioBucket>()
      byPattern.set(summary.pattern, scenarioMap)
    }
    const groupKey = makeUseCaseScenarioGroupKey(
      summary.use_case,
      summary.scenario,
    )
    let bucket = scenarioMap.get(groupKey)
    if (bucket === undefined) {
      bucket = {
        useCase: summary.use_case,
        scenario: summary.scenario,
        workflows: [],
      }
      scenarioMap.set(groupKey, bucket)
    }
    bucket.workflows.push({
      summary,
      display: workflowDisplay(summary),
    })
  }

  const patternNames = [...byPattern.keys()]
  patternNames.sort((a, b) => {
    const ia = minIndexForPattern(byPattern.get(a)!, order)
    const ib = minIndexForPattern(byPattern.get(b)!, order)
    if (ia !== ib) {
      return ia - ib
    }
    return a.localeCompare(b)
  })

  return patternNames.map((patternName) => {
    const scenarioMap = byPattern.get(patternName)!
    const useCaseScenarios: UseCaseScenarioNode[] = [...scenarioMap.values()]
      .map((bucket) => ({
        useCase: bucket.useCase,
        scenario: bucket.scenario,
        label: formatConversationLabel(bucket.scenario),
        workflows: [...bucket.workflows].sort((a, b) => {
          const ia = order.get(a.summary.name) ?? Number.POSITIVE_INFINITY
          const ib = order.get(b.summary.name) ?? Number.POSITIVE_INFINITY
          if (ia !== ib) {
            return ia - ib
          }
          return a.summary.name.localeCompare(b.summary.name)
        }),
      }))
      .sort((a, b) => {
        const ia = minIndexForWorkflows(a.workflows, order)
        const ib = minIndexForWorkflows(b.workflows, order)
        if (ia !== ib) {
          return ia - ib
        }
        return a.label.localeCompare(b.label)
      })
    return {
      name: patternName,
      useCaseScenarios,
    }
  })
}

const buildReferencePatternNames = (
  placeholders: readonly WorkflowSummary[],
  order: Map<string, number>,
): string[] => {
  const byPattern = new Map<string, number>()
  for (const row of placeholders) {
    const idx = order.get(row.name) ?? Number.POSITIVE_INFINITY
    const prev = byPattern.get(row.pattern)
    if (prev === undefined || idx < prev) {
      byPattern.set(row.pattern, idx)
    }
  }
  return [...byPattern.keys()].sort((a, b) => {
    const ia = byPattern.get(a) ?? Number.POSITIVE_INFINITY
    const ib = byPattern.get(b) ?? Number.POSITIVE_INFINITY
    if (ia !== ib) {
      return ia - ib
    }
    return a.localeCompare(b)
  })
}

/**
 * Split catalog into implemented tree + Reference Library pattern names.
 */
export const buildCatalogSidebarLayout = (
  summaries: readonly WorkflowSummary[],
): CatalogSidebarLayout => {
  const order = catalogIndexByName(summaries)
  const implementedRows = summaries.filter((s) => !isPlaceholderWorkflow(s))
  const placeholderRows = summaries.filter(isPlaceholderWorkflow)

  return {
    implementedPatterns: groupImplementedSummaries(implementedRows),
    referencePatternNames: buildReferencePatternNames(placeholderRows, order),
  }
}

/**
 * Group non-placeholder workflows only (implemented section).
 */
export const groupWorkflowsByPatternUseCaseAndScenario = (
  summaries: readonly WorkflowSummary[],
): PatternNode[] =>
  buildCatalogSidebarLayout(summaries).implementedPatterns