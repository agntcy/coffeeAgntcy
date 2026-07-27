/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared connection lifecycle for NDJSON agent-prompt stream stores
 * (auction, recruiter, and group messaging patterns).
 **/

export const NDJSON_STREAMING_STATUS = {
  IDLE: "idle",
  CONNECTING: "connecting",
  STREAMING: "streaming",
  COMPLETED: "completed",
  ERROR: "error",
} as const

export type NdjsonStreamingStatus =
  (typeof NDJSON_STREAMING_STATUS)[keyof typeof NDJSON_STREAMING_STATUS]
