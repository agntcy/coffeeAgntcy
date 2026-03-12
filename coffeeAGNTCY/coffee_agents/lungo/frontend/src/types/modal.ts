/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared modal contract: identity/badge/policy graph node modals.
 * Used by: useModalManager (state + actions), ModalContainer, and modal components
 * (IdentityModal, BadgeDetailsModal, PolicyDetailsModal).
 **/

import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

/** Modal id: which modal is open, or null when closed. */
export type ModalType = "identity" | "badge" | "policy" | null

/** Position where the modal is anchored (e.g. node click coordinates). */
export interface ModalPosition {
  x: number
  y: number
}

/** Node data passed into the modal; may include modal-only fields. */
export type ModalNodeData = (CustomNodeData & { isMcpServer?: boolean }) | null

/** Modal state: id + position + payload (node data for identity/badge/policy). */
export interface ModalState {
  activeModal: ModalType
  activeNodeData: ModalNodeData
  modalPosition: ModalPosition
}
