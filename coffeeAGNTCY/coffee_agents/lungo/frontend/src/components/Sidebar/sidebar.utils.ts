/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Sidebar-local helpers: expand/collapse keys, initial expanded state, and
 * catalog row grouping for the LHS tree (pattern -> conversation -> workflow;
 * reference library adds category -> pattern).
 */

import type {
  PatternCategory,
  WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"

/** Catalog workflow names that use a workflow header + A2A SLIM child row. */
const WORKFLOWS_WITH_A2A_SLIM_TRANSPORT_LAYER: ReadonlySet<string> = new Set([
  "Publish Subscribe",
  "Publish Subscribe Streaming",
  "Group Messaging",
])

export const A2A_SLIM_MENU_LABEL = "A2A SLIM"

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

export interface ReferenceCategoryNode {
  name: string
  patternNames: string[]
}

export interface CatalogSidebarLayout {
  implementedPatterns: PatternNode[]
  referenceCategories: ReferenceCategoryNode[]
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

const minIndexForPatternNames = (
  patternNames: readonly string[],
  order: Map<string, number>,
): number => {
  let m = Number.POSITIVE_INFINITY
  for (const name of patternNames) {
    const idx = order.get(name)
    if (idx !== undefined && idx < m) {
      m = idx
    }
  }
  return m
}

const compareCategoryNames = (
  a: string,
  b: string,
  categoryOrder: readonly string[],
): number => {
  const ia = categoryOrder.indexOf(a)
  const ib = categoryOrder.indexOf(b)
  const rankA = ia === -1 ? Number.POSITIVE_INFINITY : ia
  const rankB = ib === -1 ? Number.POSITIVE_INFINITY : ib
  if (rankA !== rankB) {
    return rankA - rankB
  }
  return a.localeCompare(b)
}

const sortCategoryNames = (
  names: Iterable<string>,
  categoryOrder: readonly string[],
  tieBreakIndex?: (name: string) => number,
): string[] =>
  [...names].sort((a, b) => {
    const byOrder = compareCategoryNames(a, b, categoryOrder)
    if (byOrder !== 0) {
      return byOrder
    }
    if (tieBreakIndex) {
      const ia = tieBreakIndex(a)
      const ib = tieBreakIndex(b)
      if (ia !== ib) {
        return ia - ib
      }
    }
    return a.localeCompare(b)
  })

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

const buildReferenceCategories = (
  placeholders: readonly WorkflowSummary[],
  order: Map<string, number>,
  categoryOrder: readonly string[],
): ReferenceCategoryNode[] => {
  const byPattern = new Map<
    string,
    { category: string; orderIndex: number }
  >()

  for (const row of placeholders) {
    const idx = order.get(row.name) ?? Number.POSITIVE_INFINITY
    const prev = byPattern.get(row.pattern)
    if (prev === undefined || idx < prev.orderIndex) {
      byPattern.set(row.pattern, {
        category: row.pattern_category,
        orderIndex: idx,
      })
    }
  }

  const byCategory = new Map<
    string,
    Array<{ name: string; orderIndex: number }>
  >()

  for (const [patternName, { category, orderIndex }] of byPattern) {
    const list = byCategory.get(category) ?? []
    list.push({ name: patternName, orderIndex })
    byCategory.set(category, list)
  }

  return sortCategoryNames(byCategory.keys(), categoryOrder, (categoryName) =>
    minIndexForPatternNames(
      (byCategory.get(categoryName) ?? []).map((entry) => entry.name),
      order,
    ),
  ).map((categoryName) => ({
    name: categoryName,
    patternNames: [...(byCategory.get(categoryName) ?? [])]
      .sort((a, b) =>
        a.orderIndex !== b.orderIndex
          ? a.orderIndex - b.orderIndex
          : a.name.localeCompare(b.name),
      )
      .map((entry) => entry.name),
  }))
}

export const patternCategoryOrderFromApi = (
  categories: readonly PatternCategory[],
): string[] => categories.map((category) => category.name)

/**
 * Split catalog into implemented tree + Reference Library categories.
 */
export const buildCatalogSidebarLayout = (
  summaries: readonly WorkflowSummary[],
  categoryOrder: readonly string[] = [],
): CatalogSidebarLayout => {
  const order = catalogIndexByName(summaries)
  const implementedRows = summaries.filter((s) => !isPlaceholderWorkflow(s))
  const placeholderRows = summaries.filter(isPlaceholderWorkflow)
  const patterns = groupImplementedSummaries(implementedRows)

  return {
    implementedPatterns: patterns,
    referenceCategories: buildReferenceCategories(
      placeholderRows,
      order,
      categoryOrder,
    ),
  }
}

/**
 * Group non-placeholder workflows only (implemented section).
 */
export const groupWorkflowsByPatternUseCaseAndScenario = (
  summaries: readonly WorkflowSummary[],
  categoryOrder: readonly string[] = [],
): PatternNode[] =>
  buildCatalogSidebarLayout(summaries, categoryOrder).implementedPatterns

export const REFERENCE_LIBRARY_KEY = "reference-library"

export const isPlaceholderWorkflow = (summary: WorkflowSummary): boolean =>
  summary.use_case === "---" && summary.scenario === "---"

export const makeReferenceCategoryKey = (categoryName: string): string =>
  `${REFERENCE_LIBRARY_KEY}|category:${categoryName}`

export const makePatternKey = (patternName: string): string =>
  `pattern:${patternName}`

export const makeUseCaseKey = (patternName: string, useCase: string): string =>
  `pattern:${patternName}|usecase:${useCase}`

export const makeScenarioKey = (
  patternName: string,
  useCase: string,
  scenario: string,
): string => `pattern:${patternName}|usecase:${useCase}|scenario:${scenario}`

/** Expandable workflow header (SLIM transport workflows only). */
export const makeWorkflowKey = (
  patternName: string,
  useCase: string,
  scenario: string,
  workflowName: string,
): string =>
  `pattern:${patternName}|usecase:${useCase}|scenario:${scenario}|workflow:${workflowName}`

const addPatternExpandedKeys = (
  next: Set<string>,
  pattern: PatternNode,
): void => {
  next.add(makePatternKey(pattern.name))
  for (const ucs of pattern.useCaseScenarios) {
    next.add(makeUseCaseKey(pattern.name, ucs.useCase))
    next.add(makeScenarioKey(pattern.name, ucs.useCase, ucs.scenario))
    for (const workflow of ucs.workflows) {
      if (workflow.display === "slim_transport") {
        next.add(
          makeWorkflowKey(
            pattern.name,
            ucs.useCase,
            ucs.scenario,
            workflow.summary.name,
          ),
        )
      }
    }
  }
}

export const buildInitialExpanded = (
  layout: Pick<CatalogSidebarLayout, "implementedPatterns" | "referenceCategories">,
): Set<string> => {
  const next = new Set<string>()

  for (const pattern of layout.implementedPatterns) {
    addPatternExpandedKeys(next, pattern)
  }

  if (layout.referenceCategories.length > 0) {
    next.add(REFERENCE_LIBRARY_KEY)
    for (const category of layout.referenceCategories) {
      next.add(makeReferenceCategoryKey(category.name))
    }
  }

  return next
}

export const groupScenariosByUseCase = (
  scenarios: readonly UseCaseScenarioNode[],
): Map<string, UseCaseScenarioNode[]> => {
  const byUseCase = new Map<string, UseCaseScenarioNode[]>()
  for (const ucs of scenarios) {
    const list = byUseCase.get(ucs.useCase)
    if (list === undefined) {
      byUseCase.set(ucs.useCase, [ucs])
    } else {
      list.push(ucs)
    }
  }
  return byUseCase
}
