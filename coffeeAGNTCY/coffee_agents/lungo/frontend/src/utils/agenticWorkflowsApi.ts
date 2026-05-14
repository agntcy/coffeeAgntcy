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

export interface WorkflowDocumentationSection {
  anchor: string
  heading: string
  body_markdown: string
}

export interface WorkflowDocumentationResponse {
  slug: string
  workflow_name: string
  title: string | null
  sections: WorkflowDocumentationSection[]
  full_markdown: string
}

export async function fetchWorkflowDocumentation(
  workflowName: string,
  signal?: AbortSignal,
): Promise<WorkflowDocumentationResponse> {
  const encoded = encodeURIComponent(workflowName)
  const url = `${getAgenticWorkflowsApiUrl()}/agentic-workflows/${encoded}/documentation/`
  const response = await fetch(url, { signal })
  if (!response.ok) {
    throw new Error(
      `Workflow documentation: HTTP ${response.status} ${response.statusText}`,
    )
  }
  return response.json() as Promise<WorkflowDocumentationResponse>
}

/** One row of `GET /agentic-workflows/` (matches backend `WorkflowSummary`). */
export interface WorkflowSummary {
  name: string
  pattern: string
  use_case: string
  scenario: string
}

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0

const isWorkflowSummary = (value: unknown): value is WorkflowSummary => {
  if (value === null || typeof value !== "object") return false
  const obj = value as Record<string, unknown>
  return (
    isNonEmptyString(obj.name) &&
    isNonEmptyString(obj.pattern) &&
    isNonEmptyString(obj.use_case) &&
    isNonEmptyString(obj.scenario)
  )
}

/**
 * Fetch the workflow summaries from `GET /agentic-workflows/`.
 *
 * The backend responds with a map keyed by workflow name (`WorkflowSummaryMapResponse`).
 * This helper flattens the map into an array in **JSON object key order** (which should
 * mirror `starting_workflows.json` when the server builds the map in file order).
 * Entries that do not match the expected shape are skipped so a single bad row cannot
 * break the sidebar.
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

  const raw = body as Record<string, unknown>
  const summaries: WorkflowSummary[] = []
  for (const key of Object.keys(raw)) {
    const value = raw[key]
    if (isWorkflowSummary(value)) {
      summaries.push(value)
    }
  }
  return summaries
}
