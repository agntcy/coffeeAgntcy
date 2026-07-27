/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * NDJSON payload frame types for recruiter (a2a-http) streams.
 * Separate from {@link NDJSON_STREAMING_STATUS} connection lifecycle.
 **/

export const RECRUITER_STREAM_EVENT_TYPE = {
  STATUS_UPDATE: "status_update",
  COMPLETED: "completed",
  ERROR: "error",
} as const

export type RecruiterStreamEventType =
  (typeof RECRUITER_STREAM_EVENT_TYPE)[keyof typeof RECRUITER_STREAM_EVENT_TYPE]
