/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared dialog contract: graph identity (dropdown) + badge/policy (OUK `Dialog`).
 * Used by: useDialogManager (state + actions), DialogContainer, and graph UI components.
 **/

import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

/** Dialog id: which dialog is open, or null when closed. */
export type DialogType = "identity" | "badge" | "policy" | null

/** Node data passed into the dialog; may include dialog-only fields. */
export type DialogNodeData = (CustomNodeData & { isMcpServer?: boolean }) | null

/** Dialog/dropdown state: id + payload (node data for identity/badge/policy). */
export interface DialogState {
  activeDialog: DialogType
  activeNodeData: DialogNodeData
}
