/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box } from "@open-ui-kit/core"
import type { SxProps, Theme } from "@mui/material/styles"
import { graphIconChipSx } from "./graphNodeSurface"

export interface GraphIconChipProps {
  children: React.ReactNode
  sx?: SxProps<Theme>
}

/** Wraps MUI icons, PNGs, or SVGs in the graph with shared chip styling. */
export function GraphIconChip({ children, sx }: GraphIconChipProps) {
  return (
    <Box
      sx={(theme) => ({
        ...graphIconChipSx(theme),
        ...(typeof sx === "function" ? sx(theme) : sx),
      })}
    >
      {children}
    </Box>
  )
}
