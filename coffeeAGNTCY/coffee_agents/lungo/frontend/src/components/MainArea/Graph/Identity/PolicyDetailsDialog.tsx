/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { CustomNodeData } from "../Elements/types"
import {
  fetchPolicyDetails,
  policyDetailsEndpointLabelForReport,
} from "./IdentityApi"
import GraphIdentityJsonDetailsDialog from "./GraphIdentityJsonDetailsDialog"

export interface PolicyDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const PolicyDetailsDialog: React.FC<PolicyDetailsDialogProps> = (props) => (
  <GraphIdentityJsonDetailsDialog
    {...props}
    titleSuffix="Policy Details"
    loadErrorTitle="Failed to load policy details"
    fetchData={fetchPolicyDetails}
    endpointLabelForReport={policyDetailsEndpointLabelForReport}
  />
)

export default PolicyDetailsDialog
