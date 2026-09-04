/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { CustomNodeData } from "../Elements/types"
import {
  badgeDetailsEndpointLabelForReport,
  fetchBadgeDetails,
} from "./IdentityApi"
import GraphIdentityJsonDetailsDialog from "./GraphIdentityJsonDetailsDialog"

interface BadgeDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const BadgeDetailsDialog: React.FC<BadgeDetailsDialogProps> = (props) => (
  <GraphIdentityJsonDetailsDialog
    {...props}
    titleSuffix="Badge Details"
    loadErrorTitle="Failed to load badge details"
    fetchData={fetchBadgeDetails}
    endpointLabelForReport={badgeDetailsEndpointLabelForReport}
  />
)

export default BadgeDetailsDialog
