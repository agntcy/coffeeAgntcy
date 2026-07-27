/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Resolve chat backend URLs from catalog WorkflowSummary capability fields.
 */

import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { getApiUrlForChatTarget } from "@/utils/patternUtils"
import {
  joinHttpRequest,
  LUNGO_FRONTEND_URLS,
  type HttpRequestTarget,
} from "@/urls"
import { isChatEnabledWorkflow } from "@/utils/workflowCapabilities"

/** Base app URL for a catalog workflow; null/invalid summary → exchange. */
export function getApiBaseUrlForWorkflow(
  summary: WorkflowSummary | null | undefined,
): string {
  return getApiUrlForChatTarget(summary?.chat_api_target ?? null)
}

/** Non-streaming POST .../agent/prompt */
export function getAgentPromptRequestForWorkflow(
  summary: WorkflowSummary | null | undefined,
): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseUrlForWorkflow(summary),
    LUNGO_FRONTEND_URLS.apiPaths.agentPrompt,
  )
}

export function getAgentPromptUrlForWorkflow(
  summary: WorkflowSummary | null | undefined,
): string {
  return getAgentPromptRequestForWorkflow(summary).url
}

/** Streaming POST .../agent/prompt/stream */
export function getAgentPromptStreamRequestForWorkflow(
  summary: WorkflowSummary | null | undefined,
): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseUrlForWorkflow(summary),
    LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream,
  )
}

export function getAgentPromptStreamUrlForWorkflow(
  summary: WorkflowSummary | null | undefined,
): string {
  return getAgentPromptStreamRequestForWorkflow(summary).url
}

/** Suggested prompts fetch target (path varies when workflow supports streaming). */
export function getSuggestedPromptsRequestForWorkflow(
  summary: WorkflowSummary | null | undefined,
): HttpRequestTarget | null {
  if (!isChatEnabledWorkflow(summary)) return null
  const base = getApiBaseUrlForWorkflow(summary)
  const route =
    summary?.supports_streaming === true
      ? LUNGO_FRONTEND_URLS.apiPaths.suggestedPromptsStreaming
      : LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts
  return joinHttpRequest(base, route)
}

/** Suggested prompts URL (streaming variant when workflow supports streaming). */
export function getSuggestedPromptsUrlForWorkflow(
  summary: WorkflowSummary | null | undefined,
): string | null {
  return getSuggestedPromptsRequestForWorkflow(summary)?.url ?? null
}

/** Retries only for group SSE workflows. */
export function shouldEnableRetriesForWorkflow(
  summary: WorkflowSummary | null | undefined,
): boolean {
  return summary?.supports_sse === true
}
