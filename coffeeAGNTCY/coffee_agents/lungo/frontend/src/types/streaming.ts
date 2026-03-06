import type { AgentRecord } from "@/types/agent"
import { GraphConfig } from "@/utils/graphConfigs"

interface LogisticsStreamStep {
  order_id: string

  sender: string

  receiver: string

  message: string

  timestamp: string

  state: string
}

interface AuctionStreamingResponse {
  response: string
  session_id?: string
}

interface GroupCommunicationFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: GraphConfig
  executionKey?: string
  apiError: boolean
}

interface AuctionStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  executionKey?: string
  apiError: boolean
  auctionStreamingState?: AuctionStreamingState
}

interface SSERetryState {
  retryCount: number
  isRetrying: boolean
  lastRetryAt: number | null
  nextRetryAt: number | null
}

interface SSEState {
  isConnected: boolean
  isConnecting: boolean
  events: LogisticsStreamStep[]
  currentOrderId: string | null
  error: string | null
  retryState: SSERetryState
}

interface AuctionStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: AuctionStreamingResponse[]
  error: string | null
}

interface RecruiterStreamingEvent {
  event_type: "status_update" | "completed" | "error"
  message: string | null
  state: "working" | "completed"
  author?: string
  agent_records?: Record<string, AgentRecord>
  evaluation_results?: Record<string, unknown>
  selected_agent?: Record<string, unknown>
}

interface RecruiterStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: RecruiterStreamingEvent[]
  error: string | null
  sessionId: string | null
  finalMessage: string | null
  agentRecords: Record<string, AgentRecord> | null
  evaluationResults: Record<string, unknown> | null
  selectedAgent: Record<string, unknown> | null
}

interface RecruiterStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  apiError: boolean
  recruiterStreamingState?: RecruiterStreamingState
}

export type {
  LogisticsStreamStep,
  AuctionStreamingResponse,
  AuctionStreamingState,
  GroupCommunicationFeedProps,
  AuctionStreamingFeedProps,
  RecruiterStreamingEvent,
  RecruiterStreamingState,
  RecruiterStreamingFeedProps,
  SSEState,
}
