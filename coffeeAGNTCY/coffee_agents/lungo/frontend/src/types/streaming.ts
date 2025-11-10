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

export type {
  LogisticsStreamStep,
  AuctionStreamingResponse,
  AuctionStreamingState,
  GroupCommunicationFeedProps,
  AuctionStreamingFeedProps,
  SSEState,
}
