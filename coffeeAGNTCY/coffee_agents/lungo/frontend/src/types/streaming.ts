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
}

interface GroupCommunicationFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: any
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
  agent_records?: Record<string, any>
  evaluation_results?: Record<string, any>
  selected_agent?: Record<string, any>
}

interface RecruiterStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: RecruiterStreamingEvent[]
  error: string | null
  sessionId: string | null
  finalMessage: string | null
  agentRecords: Record<string, any> | null
  evaluationResults: Record<string, any> | null
  selectedAgent: Record<string, any> | null
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
