/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, IconButton, Stack, Typography } from "@open-ui-kit/core"
import Visibility from "@mui/icons-material/Visibility"
import { IdentityDetailsDropdownContentProps } from "./types"
import githubIconLight from "@/assets/Github_lightmode.png"
import urlsConfig from "@/utils/urls.json"
import { SecurityClass } from "@/utils/SecurityClass"

const IdentityDetailsDropdownContent: React.FC<
  IdentityDetailsDropdownContentProps
> = ({ onShowBadgeDetails, onShowPolicyDetails, nodeData }) => {
  //TODO: change GH icon for light/dark mode
  const githubIconSrc = githubIconLight

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
          <IconButton
            onClick={onShowBadgeDetails}
            sx={{
              justifyContent: "space-between",
              gap: 1.5,
            }}
          >
            <Visibility />
          </IconButton>
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
          <IconButton
            onClick={onShowPolicyDetails}
            sx={{
              justifyContent: "space-between",
              gap: 1.5,
            }}
          >
            <Visibility />
          </IconButton>
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
            <IconButton
              onClick={() =>
                window.open(identityGithubUrl, "_blank", "noopener,noreferrer")
              }
              sx={{
                justifyContent: "space-between",
                gap: 1.5,
              }}
            >
              <Box
                component="img"
                src={githubIconSrc}
                alt="Source code"
                sx={{
                  bgcolor: "common.white",
                  maxHeight: 24,
                }}
              />
            </IconButton>
          </Stack>
        )}
    </Stack>
  )
}

export default IdentityDetailsDropdownContent
