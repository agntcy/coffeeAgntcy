/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { NdjsonStreamingStatus } from "./ndjsonStreamingStatus"
import type { SupplyChainStreamEvent } from "./supplyChainEvents"

export interface LogisticsStreamStep {
  order_id: string
  sender: string
  receiver: string
  message: string
  timestamp: string
  state: string
}

export interface GroupStreamingState {
  status: NdjsonStreamingStatus
  events: LogisticsStreamStep[]
  /** Supply Chain Commitment events (a discriminated union on `type`). */
  negotiationEvents: SupplyChainStreamEvent[]
  finalResponse: string | null
  error: string | null
  currentOrderId: string | null
  executionKey: string | null
  sessionId: string | null
}

export interface SSERetryState {
  retryCount: number
  isRetrying: boolean
  lastRetryAt: number | null
  nextRetryAt: number | null
}

export interface SSEState {
  isConnected: boolean
  isConnecting: boolean
  events: LogisticsStreamStep[]
  currentOrderId: string | null
  error: string | null
  retryState: SSERetryState
}
