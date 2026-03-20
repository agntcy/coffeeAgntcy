/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { AgentRecord } from "@/types/agent"

/** Shared shape for agent API responses (prompt, streaming completion, discovery). */
export interface ApiResponse {
  response: string
  session_id?: string
  agent_records?: Record<string, AgentRecord>
}
