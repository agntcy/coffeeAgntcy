/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export interface AuctionStreamingResponse {
  response: string
  session_id?: string
}

export interface AuctionStreamingState {
  status: "idle" | "connecting" | "streaming" | "completed" | "error"
  events: AuctionStreamingResponse[]
  error: string | null
}
