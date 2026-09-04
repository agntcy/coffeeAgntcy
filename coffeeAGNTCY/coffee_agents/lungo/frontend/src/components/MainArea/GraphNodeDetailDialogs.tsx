/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Mounts graph node detail dialogs driven by useDialogManager (badge, policy).
 * Identity UI is a node dropdown; OASF/directory is mounted separately in MainArea.
 */

import React from "react"
import BadgeDetailsDialog from "./Graph/Identity/BadgeDetailsDialog"
import PolicyDetailsDialog from "./Graph/Identity/PolicyDetailsDialog"
import type { DialogType, DialogNodeData } from "@/types/dialog"
import type { CustomNodeData } from "./Graph/Elements/types"

interface GraphNodeDetailDialogsProps {
  activeDialog: DialogType
  activeNodeData: DialogNodeData
  onClose: () => void
}

const GraphNodeDetailDialogs: React.FC<GraphNodeDetailDialogsProps> = ({
  activeDialog,
  activeNodeData,
  onClose,
}) => {
  return (
    <>
      <BadgeDetailsDialog
        isOpen={activeDialog === "badge"}
        onClose={onClose}
        nodeName={activeNodeData?.label || ""}
        nodeData={(activeNodeData ?? undefined) as CustomNodeData}
      />

      <PolicyDetailsDialog
        isOpen={activeDialog === "policy"}
        onClose={onClose}
        nodeData={(activeNodeData ?? undefined) as CustomNodeData}
        nodeName={activeNodeData?.label || ""}
      />
    </>
  )
}

export default GraphNodeDetailDialogs
