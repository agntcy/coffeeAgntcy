/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ListItemButton, Typography } from "@open-ui-kit/core"
import { sidebarLevelIndentPx } from "./sidebarLevel"
import { sidebarBorderRadius, sidebarItemMt } from "./sidebarSx"

interface SidebarItemProps {
  title: string
  level: number
  isSelected?: boolean
  onClick?: () => void
  disabled?: boolean
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  level,
  isSelected = false,
  onClick,
  disabled = false,
}) => (
  <ListItemButton
    disabled={disabled || onClick === undefined}
    onClick={onClick}
    selected={isSelected}
    sx={{
      width: "100%",
      justifyContent: "flex-start",
      pl: sidebarLevelIndentPx(level),
      pr: 2.5,
      py: 1,
      borderRadius: sidebarBorderRadius,
      mt: sidebarItemMt,
      textWrap: "auto",
      ...(disabled && { opacity: 0.5, pointerEvents: "none" }),
    }}
  >
    <Typography component="span" variant="body1">
      {title}
    </Typography>
  </ListItemButton>
)

export default SidebarItem
