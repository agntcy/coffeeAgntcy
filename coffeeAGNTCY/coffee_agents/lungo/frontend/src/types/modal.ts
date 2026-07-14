/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared modal contract: graph identity (dropdown) + badge/policy (OUK `Dialog`).
 * Used by: useModalManager (state + actions), ModalContainer, and graph UI components.
 **/

import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

/** Modal id: which modal is open, or null when closed. */
export type ModalType = "identity" | "badge" | "policy" | null

/** Node data passed into the modal; may include modal-only fields. */
export type ModalNodeData = (CustomNodeData & { isMcpServer?: boolean }) | null

/** Modal/dropdown state: id + payload (node data for identity/badge/policy). */
export interface ModalState {
  activeModal: ModalType
  activeNodeData: ModalNodeData
}
