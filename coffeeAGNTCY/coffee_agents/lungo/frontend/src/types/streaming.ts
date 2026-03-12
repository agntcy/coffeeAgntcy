import type { AuctionStreamingState } from "@/stores/auctionStreaming.types"
import { GraphConfig } from "@/utils/graphConfigs"

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

export type {
  GroupCommunicationFeedProps,
  AuctionStreamingFeedProps,
}
