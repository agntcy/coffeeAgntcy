/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

/** Shared agent/directory record shape (recruiter streaming state, etc.). */
export type AgentRecord = {
  id?: string
  name?: string
  [key: string]: unknown
}
