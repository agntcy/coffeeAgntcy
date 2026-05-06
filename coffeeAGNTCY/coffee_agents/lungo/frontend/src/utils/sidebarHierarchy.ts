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

export interface WorkflowNode {
  name: string
  slug: PatternType | null
}

export interface UseCaseNode {
  name: string
  workflows: WorkflowNode[]
}

export interface PatternNode {
  name: string
  useCases: UseCaseNode[]
}

/**
 * Group workflow summaries into the `pattern -> use-case -> workflow` tree.
 *
 * Ordering is alphabetical at every level so the menu is stable regardless of
 * the order the API happens to return rows in. Workflow names without a known
 * slug are kept in the tree (with `slug: null`) so the sidebar can render
 * them disabled.
 */
export const groupWorkflowsByPatternAndUseCase = (
  summaries: readonly WorkflowSummary[],
): PatternNode[] => {
  const byPattern = new Map<string, Map<string, WorkflowNode[]>>()

  for (const summary of summaries) {
    let useCaseMap = byPattern.get(summary.pattern)
    if (useCaseMap === undefined) {
      useCaseMap = new Map<string, WorkflowNode[]>()
      byPattern.set(summary.pattern, useCaseMap)
    }
    let workflows = useCaseMap.get(summary.use_case)
    if (workflows === undefined) {
      workflows = []
      useCaseMap.set(summary.use_case, workflows)
    }
    workflows.push({
      name: summary.name,
      slug: mapWorkflowNameToSlug(summary.name),
    })
  }

  const sortedPatternNames = [...byPattern.keys()].sort((a, b) =>
    a.localeCompare(b),
  )
  return sortedPatternNames.map((patternName) => {
    const useCaseMap = byPattern.get(patternName)!
    const sortedUseCaseNames = [...useCaseMap.keys()].sort((a, b) =>
      a.localeCompare(b),
    )
    return {
      name: patternName,
      useCases: sortedUseCaseNames.map((useCaseName) => ({
        name: useCaseName,
        workflows: [...useCaseMap.get(useCaseName)!].sort((a, b) =>
          a.name.localeCompare(b.name),
        ),
      })),
    }
  })
}
