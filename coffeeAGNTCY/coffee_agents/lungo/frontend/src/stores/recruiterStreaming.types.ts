/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { AgentRecord } from "@/types/agent"

export interface RecruiterStreamingEvent {
  event_type: "status_update" | "completed" | "error"
  message: string | null
  state: "working" | "completed"
  author?: string
  agent_records?: Record<string, AgentRecord>
  evaluation_results?: Record<string, unknown>
  selected_agent?: Record<string, unknown>
}

export interface RecruiterStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: RecruiterStreamingEvent[]
  error: string | null
  sessionId: string | null
  finalMessage: string | null
  agentRecords: Record<string, AgentRecord> | null
  evaluationResults: Record<string, unknown> | null
  selectedAgent: Record<string, unknown> | null
}

export interface RecruiterStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  apiError: boolean
  recruiterStreamingState?: RecruiterStreamingState
}
