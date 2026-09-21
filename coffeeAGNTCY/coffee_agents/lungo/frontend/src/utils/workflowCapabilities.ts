/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Single source of truth for catalog WorkflowSummary capability precedence.
 */

import { isPlaceholderWorkflow } from "@/components/Sidebar/sidebar.utils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"

export type WorkflowChatTransport =
  | "group_sse"
  | "auction_stream"
  | "recruiter_stream"
  | "plain_post"

export interface WorkflowCapabilities {
  transport: WorkflowChatTransport
  pattern: PatternType
}

export interface WorkflowChatUiMode {
  showProgressTracker: boolean
  usesAuctionStreamPanel: boolean
  usesRecruiterStreamPanel: boolean
  usesPlainFinalResponse: boolean
  isGroupMessaging: boolean
}

const TRANSPORT_TO_PATTERN: Record<WorkflowChatTransport, PatternType> = {
  group_sse: PATTERNS.GROUP_MESSAGING,
  recruiter_stream: PATTERNS.A2A_HTTP,
  auction_stream: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
  plain_post: PATTERNS.PUBLISH_SUBSCRIBE,
}

/**
 * Derive chat transport and sidebar pattern from catalog capability fields.
 * Precedence: supports_sse → discovery → supports_streaming → exchange plain post.
 */
export function deriveWorkflowCapabilities(
  summary: WorkflowSummary | null | undefined,
): WorkflowCapabilities | null {
  if (!summary || summary.chat_api_target === null) return null
  if (summary.supports_sse) {
    return {
      transport: "group_sse",
      pattern: TRANSPORT_TO_PATTERN.group_sse,
    }
  }
  if (summary.chat_api_target === "discovery") {
    return {
      transport: "recruiter_stream",
      pattern: TRANSPORT_TO_PATTERN.recruiter_stream,
    }
  }
  if (summary.supports_streaming) {
    return {
      transport: "auction_stream",
      pattern: TRANSPORT_TO_PATTERN.auction_stream,
    }
  }
  if (summary.chat_api_target === "exchange") {
    return {
      transport: "plain_post",
      pattern: TRANSPORT_TO_PATTERN.plain_post,
    }
  }
  return null
}

export function patternTypeFromSummary(
  summary: WorkflowSummary,
): PatternType | null {
  return deriveWorkflowCapabilities(summary)?.pattern ?? null
}

export function workflowChatTransport(
  summary: WorkflowSummary | null | undefined,
): WorkflowChatTransport | null {
  return deriveWorkflowCapabilities(summary)?.transport ?? null
}

export function isChatEnabledWorkflow(
  summary: WorkflowSummary | null | undefined,
): boolean {
  if (!summary || isPlaceholderWorkflow(summary)) return false
  return deriveWorkflowCapabilities(summary) !== null
}

export function workflowChatUiMode(
  summary: WorkflowSummary | null | undefined,
): WorkflowChatUiMode | null {
  const transport = workflowChatTransport(summary)
  if (!summary || transport === null) return null
  return {
    showProgressTracker: transport === "group_sse",
    usesAuctionStreamPanel: transport === "auction_stream",
    usesRecruiterStreamPanel: transport === "recruiter_stream",
    usesPlainFinalResponse: transport === "plain_post",
    isGroupMessaging: transport === "group_sse",
  }
}
