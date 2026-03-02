/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

/** Shared agent/directory record shape (discovery, recruiter streaming, etc.). */
export type AgentRecord = {
  id?: string
  name?: string
  [key: string]: unknown
}

/** Event payload when discovery completes; used to sync graph with agent_records. */
export type DiscoveryResponseEvent = {
  response: string
  ts: number
  sessionId?: string
  agent_records?: AgentRecord[]
}
