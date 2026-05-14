/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Helpers to turn a flat list of catalog `WorkflowSummary` rows into the
 * `pattern -> use-case -> workflow` tree the LHS sidebar renders, plus the
 * mapping from a catalog workflow name to the internal `PatternType` slug
 * that the rest of the frontend (graph configs, API URLs, streaming, ...)
 * keys off of.
 */

import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

/**
 * Maps a workflow `name` returned by the catalog to the internal `PatternType`
 * slug expected by downstream code (see `patternUtils.ts`, `graphConfigs.ts`).
 *
 * Workflows whose name is not present here render disabled in the sidebar so
 * the user is not silently denied access to anything the API advertises.
 *
 * If/when the backend grows a `frontend_pattern_id` (or similar) field on the
 * workflow summary, the right place to consume it is this file.
 */
export const WORKFLOW_NAME_TO_PATTERN_SLUG: Readonly<
  Record<string, PatternType>
> = {
  "Publish Subscribe Coffee Farm Network": PATTERNS.PUBLISH_SUBSCRIBE,
  "Publish Subscribe Streaming Coffee Auction Network":
    PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
  "Secure Group Communication Logistics Network": PATTERNS.GROUP_COMMUNICATION,
  "On-demand Discovery": PATTERNS.ON_DEMAND_DISCOVERY,
}

export const mapWorkflowNameToSlug = (name: string): PatternType | null => {
  return WORKFLOW_NAME_TO_PATTERN_SLUG[name] ?? null
}

/**
 * Inverse of `WORKFLOW_NAME_TO_PATTERN_SLUG`: maps an implemented graph
 * `PatternType` to the catalog `Workflow.name` used by
 * `GET /agentic-workflows/{workflow_name}/documentation/`.
 *
 * Patterns without a graph (`no_workflow_implementation`) are not listed.
 */
const PATTERN_SLUG_TO_WORKFLOW_NAME: Partial<Record<PatternType, string>> = {}
for (const [workflowName, slug] of Object.entries(
  WORKFLOW_NAME_TO_PATTERN_SLUG,
) as [string, PatternType][]) {
  PATTERN_SLUG_TO_WORKFLOW_NAME[slug] = workflowName
}

export function getCatalogWorkflowNameForPattern(
  pattern: PatternType,
): string | null {
  if (pattern === PATTERNS.NO_WORKFLOW_IMPLEMENTATION) {
    return null
  }
  return PATTERN_SLUG_TO_WORKFLOW_NAME[pattern] ?? null
}

export interface WorkflowNode {
  name: string
  slug: PatternType | null
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

/** One row in the LHS catalog: either a pattern subtree or a visual separator. */
export type CatalogSidebarEntry =
  | {
      kind: "pattern"
      node: PatternNode
      /** `implemented` = full dropdown tree; `placeholder` = pattern button only. */
      variant: "implemented" | "placeholder"
    }
  | { kind: "separator" }

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

/**
 * Internal accumulator used while grouping workflow rows by their
 * `(use_case, scenario)` composite key. One bucket holds all the workflows
 * that share that pair within a given pattern.
 */
interface UseCaseScenarioBucket {
  useCase: string
  scenario: string
  workflows: WorkflowNode[]
}

/** True if this pattern has at least one implemented workflow. */
const patternHasImplementation = (pattern_node: PatternNode): boolean => {
  for (const use_case_scenario of pattern_node.useCaseScenarios) {
    for (const workflow of use_case_scenario.workflows) {
      if (pattern_node.name !== workflow.name) {
        return true
      }
    }
  }
  return false
}

const sortPatternNamesByCatalogOrder = (
  names: string[],
  byPattern: Map<string, Map<string, UseCaseScenarioBucket>>,
  order: Map<string, number>,
): string[] =>
  [...names].sort((a, b) => {
    const ia = minIndexForPattern(byPattern.get(a)!, order)
    const ib = minIndexForPattern(byPattern.get(b)!, order)
    if (ia !== ib) {
      return ia - ib
    }
    return a.localeCompare(b)
  })

const buildPatternNode = (
  patternName: string,
  byPattern: Map<string, Map<string, UseCaseScenarioBucket>>,
  order: Map<string, number>,
): PatternNode => {
  const scenarioMap = byPattern.get(patternName)!
  const useCaseScenarios: UseCaseScenarioNode[] = [...scenarioMap.values()]
    .map((bucket) => ({
      useCase: bucket.useCase,
      scenario: bucket.scenario,
      label: formatUseCaseScenarioLabel(bucket.useCase, bucket.scenario),
      workflows: [...bucket.workflows].sort((a, b) => {
        const ia = order.get(a.name) ?? Number.POSITIVE_INFINITY
        const ib = order.get(b.name) ?? Number.POSITIVE_INFINITY
        if (ia !== ib) {
          return ia - ib
        }
        return a.name.localeCompare(b.name)
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
  return { name: patternName, useCaseScenarios }
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
 * Group workflow summaries into sidebar rows: **implemented** patterns first
 * (any non-``---`` use-case/scenario bucket), optional **separator**, then
 * **placeholder** patterns (only ``---`` use-case and/or scenario buckets).
 *
 * Within each tier, order follows ``summaries`` catalog indices (see
 * ``starting_workflows.json`` / ``GET /agentic-workflows/``). Tie-break with
 * ``localeCompare`` on pattern name. Workflows without a known ``PatternType``
 * slug stay in the tree with ``slug: null``.
 */
export const groupWorkflowsByPatternAndUseCase = (
  summaries: readonly WorkflowSummary[],
): CatalogSidebarEntry[] => {
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
      name: summary.name,
      slug: mapWorkflowNameToSlug(summary.name),
    })
  }

  const allNames = [...byPattern.keys()]
  const implementedNames = sortPatternNamesByCatalogOrder(
    allNames.filter((n) =>
      patternHasImplementation(buildPatternNode(n, byPattern, order)),
    ),
    byPattern,
    order,
  )
  const placeholderNames = sortPatternNamesByCatalogOrder(
    allNames.filter(
      (n) => !patternHasImplementation(buildPatternNode(n, byPattern, order)),
    ),
    byPattern,
    order,
  )

  const out: CatalogSidebarEntry[] = implementedNames.map((patternName) => ({
    kind: "pattern",
    node: buildPatternNode(patternName, byPattern, order),
    variant: "implemented",
  }))

  if (out.length > 0 && placeholderNames.length > 0) {
    out.push({ kind: "separator" })
  }

  out.push(
    ...placeholderNames.map((patternName) => ({
      kind: "pattern" as const,
      node: buildPatternNode(patternName, byPattern, order),
      variant: "placeholder" as const,
    })),
  )

  return out
}
