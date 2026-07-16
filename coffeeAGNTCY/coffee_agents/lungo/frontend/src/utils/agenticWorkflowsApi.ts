/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Thin client for the Lungo Agentic Workflows API catalog endpoints.
 * Today only the workflow-summary listing is consumed; patterns and use-cases
 * are derived client-side from the distinct values seen across summaries.
 *
 * Catalog `WorkflowSummary` carries `supports_sse`, `supports_streaming`, and
 * `chat_api_target` for routing. `PatternType` is derived from those capability
 * fields (no static workflow-name map), with a legacy fallback for catalog rows
 * served before the capability fields existed.
 */

import { agenticWorkflowsAuthHeaders } from "@/api/agenticWorkflowsClient"
import {
  buildAgenticWorkflowsCatalogUrl,
  getAgenticWorkflowsApiUrl,
  LUNGO_FRONTEND_URLS,
} from "@/urls"
import { type ChatApiTarget, type PatternType } from "@/utils/patternUtils"
import { patternTypeFromSummary } from "@/utils/workflowCapabilities"

export type { ChatApiTarget }

/** One row of `GET /agentic-workflows/` (matches backend `WorkflowSummary`). */
export interface WorkflowSummary {
  name: string
  pattern: string
  use_case: string
  scenario: string
  supports_sse: boolean
  supports_streaming: boolean
  chat_api_target: ChatApiTarget | null
}

/** Log label / relative path for catalog requests (matches router mount). */
export const AGENTIC_WORKFLOWS_CATALOG_LOG_PATH =
  LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsCatalog

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

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.length > 0

const isChatApiTarget = (value: unknown): value is ChatApiTarget =>
  value === "exchange" || value === "logistics" || value === "discovery"

const parseChatApiTarget = (
  obj: Record<string, unknown>,
): ChatApiTarget | null => {
  const target = obj.chat_api_target
  return isChatApiTarget(target) ? target : null
}

/**
 * Normalize one catalog row; returns null when required string fields are missing.
 * Missing `supports_sse` / `supports_streaming` are treated as legacy (default false).
 */
const parseWorkflowSummaryRow = (value: unknown): WorkflowSummary | null => {
  if (value === null || typeof value !== "object") return null
  const obj = value as Record<string, unknown>
  if (
    !isNonEmptyString(obj.name) ||
    !isNonEmptyString(obj.pattern) ||
    !isNonEmptyString(obj.use_case) ||
    !isNonEmptyString(obj.scenario)
  ) {
    return null
  }
  const name = obj.name
  return {
    name,
    pattern: obj.pattern,
    use_case: obj.use_case,
    scenario: obj.scenario,
    supports_sse:
      typeof obj.supports_sse === "boolean" ? obj.supports_sse : false,
    supports_streaming:
      typeof obj.supports_streaming === "boolean"
        ? obj.supports_streaming
        : false,
    chat_api_target: parseChatApiTarget(obj),
  }
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
  const url = buildAgenticWorkflowsCatalogUrl()
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
    const row = parseWorkflowSummaryRow(raw[key])
    if (row) {
      summaries.push(row)
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

export class WorkflowDocumentationNotFoundError extends Error {
  constructor(workflowName: string) {
    super(`Workflow documentation not found for: ${workflowName}`)
    this.name = "WorkflowDocumentationNotFoundError"
  }
}

export interface WorkflowDocumentation {
  workflow_name: string
  title: string
  full_markdown: string
}

export const fetchWorkflowDocumentation = async (
  workflowName: string,
  signal?: AbortSignal,
): Promise<WorkflowDocumentation> => {
  const url = `${getAgenticWorkflowsApiUrl()}/agentic-workflows/${encodeURIComponent(workflowName)}/documentation/`
  const response = await fetch(url, {
    signal,
    headers: {
      Accept: "application/json",
      ...agenticWorkflowsAuthHeaders(),
    },
  })

  if (response.status === 404) {
    throw new WorkflowDocumentationNotFoundError(workflowName)
  }
  if (!response.ok) {
    throw new Error(
      `Failed to fetch workflow documentation: HTTP ${response.status} ${response.statusText}`,
    )
  }

  const body: unknown = await response.json()
  if (
    body === null ||
    typeof body !== "object" ||
    !("workflow_name" in body) ||
    !("title" in body) ||
    !("full_markdown" in body)
  ) {
    throw new Error(
      "Failed to fetch workflow documentation: unexpected response shape",
    )
  }

  const doc = body as WorkflowDocumentation
  return doc
}

export const pickDefaultWorkflowSummaryForPattern = (
  rows: WorkflowSummary[],
  pattern: PatternType,
): WorkflowSummary | null => {
  const matches = rows.filter((s) => patternTypeFromSummary(s) === pattern)
  if (matches.length === 0) return null
  matches.sort((a, b) => {
    const byName = a.name.localeCompare(b.name)
    if (byName !== 0) return byName
    return a.scenario.localeCompare(b.scenario)
  })
  return matches[0] ?? null
}
