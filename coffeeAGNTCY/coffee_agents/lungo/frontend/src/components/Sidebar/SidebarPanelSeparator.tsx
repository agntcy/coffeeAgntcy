/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Separator } from "react-resizable-panels"
import { styled } from "@mui/material/styles"

const StyledSeparator = styled(Separator)(({ theme }) => ({
  flexShrink: 0,
  width: 4,
  margin: 0,
  padding: 0,
  border: 0,
  backgroundColor: "transparent",
  transition: theme.transitions.create("background-color", {
    duration: theme.transitions.duration.shortest,
  }),
  "&:hover": {
    backgroundColor: theme.palette.divider,
  },
  "&:focus-visible": {
    outline: `2px solid ${theme.palette.primary.main}`,
    outlineOffset: -2,
  },
}))

const SidebarPanelSeparator: React.FC = () => (
  <StyledSeparator
    id="sidebar-panel-separator"
    aria-label="Resize workflow catalog"
  />
)

export default SidebarPanelSeparator
