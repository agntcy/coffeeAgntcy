/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export type AgentRecord = {
    id?: string
    name?: string
    [key: string]: unknown
}

export type DiscoveryResponseEvent = {
    response: string
    ts: number
    sessionId?: string
    agent_records?: AgentRecord[]
}
