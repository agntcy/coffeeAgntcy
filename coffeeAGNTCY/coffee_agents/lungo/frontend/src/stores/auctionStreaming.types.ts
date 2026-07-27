/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { NdjsonStreamingStatus } from "./ndjsonStreamingStatus"

export interface AuctionStreamingResponse {
  response: string
  session_id?: string
}

export interface AuctionStreamingState {
  status: NdjsonStreamingStatus
  events: AuctionStreamingResponse[]
  error: string | null
  sessionId?: string | null
}
