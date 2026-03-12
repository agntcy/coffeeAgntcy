import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"

interface AuctionStreamingFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  executionKey?: string
  apiError: boolean
  auctionStreamingState?: AuctionStreamingState
}

export type { AuctionStreamingFeedProps }
