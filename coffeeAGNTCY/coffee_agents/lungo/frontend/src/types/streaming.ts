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
  sseState?: {
    isConnected: boolean
    isConnecting: boolean
    events: LogisticsStreamStep[]
    currentOrderId: string | null
    error: string | null
    clearEvents: () => void
  }
}

interface AuctionStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  executionKey?: string
  apiError: boolean
  sseState?: {
    isConnected: boolean
    isConnecting: boolean
    events: AuctionStreamingResponse[]
    error: string | null
    clearEvents: () => void
  }
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

interface StreamingLogsSSEState {
  isConnected: boolean
  isConnecting: boolean
  events: AuctionStreamingResponse[]
  error: string | null
  retryState: SSERetryState
}

interface AuctionStreamingSSEState {
  isConnected: boolean
  isConnecting: boolean
  events: AuctionStreamingResponse[]
  error: string | null
  retryState: SSERetryState
}

export type {
  LogisticsStreamStep,
  AuctionStreamingResponse,
  StreamingLogsSSEState,
  AuctionStreamingSSEState,
  GroupCommunicationFeedProps,
  AuctionStreamingFeedProps,
  SSEState,
}
