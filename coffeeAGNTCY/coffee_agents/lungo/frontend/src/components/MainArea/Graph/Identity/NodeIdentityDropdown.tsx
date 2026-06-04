/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Identity menu anchored on the graph node side stack (replaces a separate info trigger).
 */

import React from "react"
import AssignmentTurnedIn from "@mui/icons-material/AssignmentTurnedIn"
import { Box } from "@open-ui-kit/core"
import { IconButtonDropdown } from "@/components/IconButtonDropdown"
import { GraphSideIconTooltip } from "@/components/MainArea/Graph/Elements/GraphSideIconTooltip"
import { graphSideIconButtonSxWithModal } from "@/components/MainArea/Graph/Elements/graphNodeSurface"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import IdentityDetailsDropdownContent from "./IdentityDetailsDropdownContent"

export interface NodeIdentityDropdownProps {
  nodeId: string
  data: CustomNodeData
}

const stopGraphPointerEvent = (event: React.SyntheticEvent) => {
  event.stopPropagation()
}

export const NodeIdentityDropdown: React.FC<NodeIdentityDropdownProps> = ({
  nodeId,
  data,
}) => {
  if (data.verificationStatus !== "verified") {
    return null
  }

  return (
    <GraphSideIconTooltip title="View agent identity details">
      <Box
        component="span"
        sx={{ display: "inline-flex" }}
        onClick={stopGraphPointerEvent}
        onMouseDown={stopGraphPointerEvent}
      >
        <IconButtonDropdown
          ariaLabel="Open identity details"
          open={Boolean(data.isIdentityDropdownOpen)}
          onOpenChange={(next) => {
            if (next) {
              data.onOpenIdentityModal?.(nodeId, data)
            } else {
              data.onCloseIdentityDropdown?.()
            }
          }}
          trigger={{
            icon: <AssignmentTurnedIn />,
            iconButtonProps: {
              sx: (t) => graphSideIconButtonSxWithModal(t),
            },
          }}
          closeOnContentClick={false}
          menuProps={{
            slotProps: {
              paper: {
                sx: { minWidth: 260, maxWidth: 360, padding: 0, zIndex: 1500 },
              },
            },
          }}
        >
          <IdentityDetailsDropdownContent
            nodeData={data}
            onShowBadgeDetails={() => data.onShowBadgeDetails?.()}
            onShowPolicyDetails={() => data.onShowPolicyDetails?.()}
          />
        </IconButtonDropdown>
      </Box>
    </GraphSideIconTooltip>
  )
}

export default NodeIdentityDropdown
