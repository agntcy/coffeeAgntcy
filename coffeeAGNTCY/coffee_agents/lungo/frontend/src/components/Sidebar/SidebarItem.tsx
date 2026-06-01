/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ListItem, ListItemButton, Typography } from "@open-ui-kit/core"
import {
  sidebarBorderRadius,
  sidebarItemMarginTop,
  sidebarListItemButtonSx,
  sidebarListItemSx,
} from "./sidebarSx"

interface SidebarItemProps {
  title: string
  isSelected?: boolean
  onClick?: () => void
  disabled?: boolean
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  isSelected = false,
  onClick,
  disabled = false,
}) => (
  <ListItem
    component="div"
    disablePadding
    sx={{
      width: "100%",
      mt: sidebarItemMarginTop,
      ...sidebarListItemSx,
    }}
  >
    <ListItemButton
      component={onClick !== undefined ? "button" : "div"}
      type={onClick !== undefined ? "button" : undefined}
      disabled={disabled || onClick === undefined}
      onClick={onClick}
      selected={isSelected}
      sx={{
        ...sidebarListItemButtonSx,
        justifyContent: "flex-start",
        borderRadius: sidebarBorderRadius,
        textWrap: "auto",
        ...(disabled && { opacity: 0.5, pointerEvents: "none" }),
      }}
    >
      <Typography component="span" variant="body1">
        {title}
      </Typography>
    </ListItemButton>
  </ListItem>
)

export default SidebarItem
