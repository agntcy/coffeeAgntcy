/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export interface LogisticsStreamStep {
  order_id: string
  sender: string
  receiver: string
  message: string
  timestamp: string
  state: string
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
