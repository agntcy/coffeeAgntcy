import { GraphConfig } from "@/utils/graphConfigs"

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

interface AuctionStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: AuctionStreamingResponse[]
  error: string | null
}

export type {
  AuctionStreamingResponse,
  AuctionStreamingState,
  GroupCommunicationFeedProps,
  AuctionStreamingFeedProps,
}
