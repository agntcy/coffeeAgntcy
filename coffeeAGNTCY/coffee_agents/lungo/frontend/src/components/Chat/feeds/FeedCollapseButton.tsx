/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Single toggle for showing or hiding expanded feed details (expand + collapse).
 * {@link AuctionStreamingFeed} does not use this: it has no expand/collapse state.
 **/

import React from "react"
import ExpandLess from "@mui/icons-material/ExpandLess"
import ExpandMore from "@mui/icons-material/ExpandMore"
import { Box, ListItemButton, Typography } from "@open-ui-kit/core"
import type { SxProps, Theme } from "@mui/material/styles"

export interface FeedCollapseButtonProps {
  /** When true, details are visible and the control shows collapse affordance. */
  expanded: boolean
  onToggle: () => void
  /** Label when details are hidden (e.g. "View details"). */
  expandLabel: string
  /** Label when details are visible (e.g. "Collapse details"). */
  collapseLabel: string
  sx?: SxProps<Theme>
}

const defaultSx: SxProps<Theme> = {
  mt: 1,
  display: "inline-flex",
  flexDirection: "row",
  alignItems: "center",
  gap: 0.5,
  borderRadius: 1,
  width: "auto",
  textAlign: "left",
}

export function FeedCollapseButton({
  expanded,
  onToggle,
  expandLabel,
  collapseLabel,
  sx,
}: FeedCollapseButtonProps): React.ReactElement {
  const mergedSx = (sx ? [defaultSx, sx] : defaultSx) as SxProps<Theme>

  return (
    <ListItemButton
      component="button"
      type="button"
      onClick={onToggle}
      aria-expanded={expanded}
      sx={mergedSx}
    >
      <Box
        component="span"
        aria-hidden
        sx={{
          display: "inline-flex",
          flex: "none",
          alignItems: "center",
        }}
      >
        {expanded ? <ExpandLess /> : <ExpandMore />}
      </Box>
      <Typography
        variant="body2"
        component="span"
        sx={expanded ? undefined : { flex: 1, minWidth: 0 }}
      >
        {expanded ? collapseLabel : expandLabel}
      </Typography>
    </ListItemButton>
  )
}
