/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, Tooltip, type TooltipProps } from "@open-ui-kit/core"

export interface GraphSideIconTooltipProps {
  title: string
  placement?: TooltipProps["placement"]
  children: React.ReactElement
}

export const GraphSideIconTooltip: React.FC<GraphSideIconTooltipProps> = ({
  title,
  placement = "left",
  children,
}) => (
  <Tooltip title={title} placement={placement} arrow>
    <Box component="span" sx={{ display: "inline-flex" }}>
      {children}
    </Box>
  </Tooltip>
)
