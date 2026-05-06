/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Thin client for the Lungo Agentic Workflows API catalog endpoints.
 * Today only the workflow-summary listing is consumed; patterns and use-cases
 * are derived client-side from the distinct values seen across summaries.
 */

import { env } from "@/utils/env"

const DEFAULT_AGENTIC_WORKFLOWS_API_URL = "http://127.0.0.1:9105"

export const getAgenticWorkflowsApiUrl = (): string => {
  return (
    env.get("VITE_AGENTIC_WORKFLOWS_API_URL") ||
    DEFAULT_AGENTIC_WORKFLOWS_API_URL
  )
}

/** One row of `GET /agentic-workflows/` (matches backend `WorkflowSummary`). */
export interface WorkflowSummary {
  name: string
  pattern: string
  use_case: string
}

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0

const isWorkflowSummary = (value: unknown): value is WorkflowSummary => {
  if (value === null || typeof value !== "object") return false
  const obj = value as Record<string, unknown>
  return (
    isNonEmptyString(obj.name) &&
    isNonEmptyString(obj.pattern) &&
    isNonEmptyString(obj.use_case)
  )
}

/**
 * Fetch the workflow summaries from `GET /agentic-workflows/`.
 *
 * The backend responds with a map keyed by workflow name (`WorkflowSummaryMapResponse`).
 * This helper flattens the map into an array, dropping any entries that do not
 * match the expected shape so a single bad row cannot break the sidebar.
 */
export const fetchWorkflowSummaries = async (
  signal?: AbortSignal,
): Promise<WorkflowSummary[]> => {
  const url = `${getAgenticWorkflowsApiUrl()}/agentic-workflows/`
  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new Error(
      `Failed to fetch agentic workflows: HTTP ${response.status} ${response.statusText}`,
    )
  }

  const body: unknown = await response.json()
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    throw new Error(
      "Failed to fetch agentic workflows: unexpected response shape",
    )
  }

  const summaries: WorkflowSummary[] = []
  for (const value of Object.values(body as Record<string, unknown>)) {
    if (isWorkflowSummary(value)) {
      summaries.push(value)
    }
  }
  return summaries
}
