/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { SecurityClass } from "@/utils/SecurityClass"
import { Box } from "@open-ui-kit/core"
import { Chip } from "@mui/material"

interface ExternalLinkButtonProps {
  url: string
  label: string
  iconSrc: string
}

const ExternalLinkButton: React.FC<ExternalLinkButtonProps> = ({
  url,
  label,
  iconSrc,
}) => {
  if (!SecurityClass.isSafeExternalUrl(url)) return null
  return (
    <Chip
      component="a"
      label={label}
      icon={
        <Box
          component="img"
          src={iconSrc}
          width={14}
          height={14}
          alt={label}
          aria-hidden
        />
      }
      onClick={() => window.open(url, "_blank")}
      target="_blank"
      rel="noopener noreferrer"
    />
  )
}

export default ExternalLinkButton
