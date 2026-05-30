/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { SecurityClass } from "@/utils/SecurityClass"
import { Box } from "@open-ui-kit/core"
import { Chip } from "@mui/material"

interface ExternalLinkButtonProps {
  component?: "a" | "button"
  url: string
  label: string
  iconSrc: string
}

const ExternalLinkButton: React.FC<ExternalLinkButtonProps> = ({
  component = "a",
  url,
  label,
  iconSrc,
}) => {
  if (!SecurityClass.isSafeExternalUrl(url)) return null
  return (
    <Chip
      component={component}
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
      {...(component === "a"
        ? {
            href: url,
            target: "_blank",
            rel: "noopener noreferrer",
          }
        : {
            onClick: () => window.open(url, "_blank", "noopener noreferrer"),
          })}
    />
  )
}

export default ExternalLinkButton
