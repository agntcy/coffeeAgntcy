/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Separator } from "react-resizable-panels"
import { alpha, styled } from "@mui/material/styles"

const StyledSeparator = styled(Separator)(({ theme }) => {
  const isLight = theme.palette.mode === "light"
  const restingOpacity = isLight ? 0.18 : 0.22
  const hoverOpacity = isLight ? 0.32 : 0.38

  return {
    flexShrink: 0,
    width: 4,
    margin: 0,
    padding: 0,
    border: 0,
    backgroundColor: alpha(theme.palette.text.primary, restingOpacity),
    cursor: "col-resize",
    transition: theme.transitions.create("background-color", {
      duration: theme.transitions.duration.shortest,
    }),
    "&:hover": {
      backgroundColor: alpha(theme.palette.text.primary, hoverOpacity),
    },
    "&:focus-visible": {
      outline: `2px solid ${theme.palette.primary.main}`,
      outlineOffset: -2,
    },
  }
})

const SidebarPanelSeparator: React.FC = () => (
  <StyledSeparator
    id="sidebar-panel-separator"
    aria-label="Resize workflow catalog"
  />
)

export default SidebarPanelSeparator
