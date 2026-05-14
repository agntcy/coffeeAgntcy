/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"

/** Bridges the agentic-workflows instance id from the graph bootstrap hook to
 *  sibling streaming stores so the agent tags emitted events with the same id
 *  the SSE listener is subscribed under. */
interface ActiveWorkflowInstanceState {
  workflowInstanceId: string | null
  setWorkflowInstanceId: (id: string | null) => void
}

export const useActiveWorkflowInstanceStore =
  create<ActiveWorkflowInstanceState>((set) => ({
    workflowInstanceId: null,
    setWorkflowInstanceId: (id) => set({ workflowInstanceId: id }),
  }))
