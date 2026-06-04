/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Thin client for the Lungo Agentic Workflows API catalog endpoints.
 * Today only the workflow-summary listing is consumed; patterns and use-cases
 * are derived client-side from the distinct values seen across summaries.
 *
 * Maps catalog `WorkflowSummary.name` to Lungo `PatternType` for chat/graph
 * routing until the API exposes an explicit slug aligned with stored workflow fields.
 *
 * Known limitation: `WORKFLOW_NAME_TO_PATTERN_SLUG` must stay aligned with backend
 * catalog display names; drift turns agentic graph mode off for a workflow with no
 * compile-time guard here. Replacing this map with an API-provided slug is deferred
 * until catalog/schema work lands and the API exposes that slug.
 */

import { agenticWorkflowsAuthHeaders } from "@/api/agenticWorkflowsClient"
import { env } from "@/utils/env"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

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
  scenario: string
}

/** Log label / relative path for catalog requests (matches router mount). */
export const AGENTIC_WORKFLOWS_CATALOG_LOG_PATH = "/agentic-workflows/"

const CATALOG_FETCH_MAX_RETRIES = 2
const CATALOG_FETCH_RETRY_DELAY_MS = 750

const sleep = (ms: number, signal: AbortSignal): Promise<void> =>
  new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"))
      return
    }
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DOMException("Aborted", "AbortError"))
    }
    signal.addEventListener("abort", onAbort, { once: true })
  })

export const WORKFLOW_NAME_TO_PATTERN_SLUG: Readonly<
  Record<string, PatternType>
> = {
  "Publish Subscribe": PATTERNS.PUBLISH_SUBSCRIBE,
  "Publish Subscribe Streaming": PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
  "Group Messaging": PATTERNS.GROUP_MESSAGING,
  "A2A HTTP": PATTERNS.A2A_HTTP,
}

export const mapWorkflowNameToSlug = (name: string): PatternType | null =>
  WORKFLOW_NAME_TO_PATTERN_SLUG[name] ?? null

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
  const response = await fetch(url, {
    signal,
    headers: {
      Accept: "application/json",
      ...agenticWorkflowsAuthHeaders(),
    },
  })
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

/**
 * Fetch the workflow catalog with retries (same AbortSignal for attempt + backoff).
 */
export const fetchWorkflowSummariesWithRetry = async (
  signal: AbortSignal,
): Promise<WorkflowSummary[]> => {
  let lastError: unknown
  for (let attempt = 0; attempt <= CATALOG_FETCH_MAX_RETRIES; attempt += 1) {
    try {
      return await fetchWorkflowSummaries(signal)
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") throw err
      lastError = err
      if (attempt < CATALOG_FETCH_MAX_RETRIES) {
        await sleep(CATALOG_FETCH_RETRY_DELAY_MS, signal)
      }
    }
  }
  throw lastError
}

export const pickDefaultWorkflowSummaryForPattern = (
  rows: WorkflowSummary[],
  pattern: PatternType,
): WorkflowSummary | null => {
  const matches = rows.filter((s) => mapWorkflowNameToSlug(s.name) === pattern)
  if (matches.length === 0) return null
  matches.sort((a, b) => {
    const byName = a.name.localeCompare(b.name)
    if (byName !== 0) return byName
    return a.scenario.localeCompare(b.scenario)
  })
  return matches[0] ?? null
}
