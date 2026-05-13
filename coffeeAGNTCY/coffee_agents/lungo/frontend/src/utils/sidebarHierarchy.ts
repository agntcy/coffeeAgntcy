/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Helpers to turn a flat list of catalog `WorkflowSummary` rows into the
 * tree the LHS sidebar renders (`pattern -> use-case + scenario -> workflow`).
 */

import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"

export interface WorkflowNode {
  summary: WorkflowSummary
}

export interface UseCaseScenarioNode {
  useCase: string
  scenario: string
  /** Display label rendered as the middle row of the LHS menu. */
  label: string
  workflows: WorkflowNode[]
}

export interface PatternNode {
  name: string
  useCaseScenarios: UseCaseScenarioNode[]
}

/** Build the display label for the middle (use-case + scenario) row. */
export const formatUseCaseScenarioLabel = (
  useCase: string,
  scenario: string,
): string => `${useCase}: ${scenario}`

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
    const idx = order.get(w.name)
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

/**
 * Group workflow summaries into the `catalog pattern -> (use-case + scenario) -> workflow` tree.
 *
 * Ordering follows the order of rows in ``summaries`` (intended to mirror
 * ``starting_workflows.json`` via ``GET /agentic-workflows/``): patterns,
 * use-case groups, and workflows are ordered by the smallest catalog index among
 * descendants, with ``localeCompare`` only as a tie-breaker. Workflow names without
 * a known slug stay in the tree with ``slug: null`` so the sidebar can render them disabled.
 */
export const groupWorkflowsByPatternUseCaseAndScenario = (
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
    bucket.workflows.push({ summary })
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
        label: formatUseCaseScenarioLabel(bucket.useCase, bucket.scenario),
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
