/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { IconButton, Stack, Typography } from "@open-ui-kit/core"
import { GraphSideIconTooltip } from "@/components/MainArea/Graph/Elements/GraphSideIconTooltip"
import Visibility from "@mui/icons-material/Visibility"
import { IdentityDetailsDropdownContentProps } from "./types"
import { useGithubIcon } from "@/hooks/useGithubIcon"
import { AssetPngIcon } from "@/components/AssetPngIcon"
import urlsConfig from "@/utils/urls.json"
import { SecurityClass } from "@/utils/SecurityClass"
import { graphSideIconButtonSx } from "@/components/MainArea/Graph/Elements/graphNodeSurface"

const IdentityDetailsDropdownContent: React.FC<
  IdentityDetailsDropdownContentProps
> = ({ onShowBadgeDetails, onShowPolicyDetails, nodeData }) => {
  const githubIconSrc = useGithubIcon()

  const getIdentityGithubUrl = () => {
    if (!nodeData) return null

    const nodeName = nodeData.label1 || ""

    if (
      nodeName.toLowerCase().includes("colombia") ||
      nodeName.toLowerCase().includes("vietnam")
    ) {
      return urlsConfig.identity.colombia
    }

    if (nodeName.toLowerCase().includes("auction")) {
      return urlsConfig.identity.auction
    }

    if (nodeData.label2?.toLowerCase().includes("payment")) {
      return urlsConfig.identity.payment
    }

    return nodeData.githubLink
  }

  const identityGithubUrl = getIdentityGithubUrl()

  return (
    <Stack
      sx={{
        width: 1,
        minWidth: 240,
        flexDirection: "column",
        gap: 0.5,
        overflowY: "auto",
        borderRadius: 1,
        border: "1px solid",
        borderColor: "divider",
        p: 1.5,
      }}
    >
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Agent Identity Details
      </Typography>

      {nodeData?.hasBadgeDetails && (
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
        >
          <Typography variant="body2" sx={{ textAlign: "left" }}>
            Badge details
          </Typography>
          <GraphSideIconTooltip title="View badge details">
            <IconButton
              onClick={onShowBadgeDetails}
              aria-label="View badge details"
              sx={(t) => graphSideIconButtonSx(t)}
            >
              <Visibility />
            </IconButton>
          </GraphSideIconTooltip>
        </Stack>
      )}

      {nodeData?.hasPolicyDetails && (
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
        >
          <Typography variant="body2" sx={{ textAlign: "left" }}>
            Policy details
          </Typography>
          <GraphSideIconTooltip title="View policy details">
            <IconButton
              onClick={onShowPolicyDetails}
              aria-label="View policy details"
              sx={(t) => graphSideIconButtonSx(t)}
            >
              <Visibility />
            </IconButton>
          </GraphSideIconTooltip>
        </Stack>
      )}

      {identityGithubUrl &&
        SecurityClass.isSafeExternalUrl(identityGithubUrl) && (
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            <Typography variant="body2" sx={{ textAlign: "left" }}>
              Source code
            </Typography>
            <GraphSideIconTooltip title="Open source code on GitHub">
              <IconButton
                onClick={() =>
                  window.open(identityGithubUrl, "_blank", "noopener,noreferrer")
                }
                aria-label="Open source code on GitHub"
                sx={(t) => graphSideIconButtonSx(t)}
              >
                <AssetPngIcon bare src={githubIconSrc} alt="Source code" />
              </IconButton>
            </GraphSideIconTooltip>
          </Stack>
        )}
    </Stack>
  )
}

export default IdentityDetailsDropdownContent
