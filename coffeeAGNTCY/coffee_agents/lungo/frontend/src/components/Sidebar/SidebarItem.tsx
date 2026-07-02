/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ListItem, ListItemButton, Typography } from "@open-ui-kit/core"
import {
  sidebarBorderRadius,
  sidebarItemButtonSx,
  sidebarItemMarginTop,
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
}) => {
  const isRowDisabled = disabled || onClick === undefined

  return (
    <ListItem
      component="div"
      disablePadding
      sx={() => ({
        width: "100%",
        mt: sidebarItemMarginTop,
        ...sidebarListItemSx(),
      })}
    >
      <ListItemButton
        component={!isRowDisabled ? "button" : "div"}
        disabled={isRowDisabled}
        aria-disabled={isRowDisabled || undefined}
        aria-label={isRowDisabled ? `${title}, unavailable` : undefined}
        onClick={!disabled ? onClick : undefined}
        selected={isSelected}
        sx={(theme) => ({
          ...sidebarItemButtonSx(theme),
          width: "100%",
          minWidth: 0,
          justifyContent: "flex-start",
          borderRadius: sidebarBorderRadius(theme),
          textWrap: "auto",
          ...(disabled && { opacity: 0.5 }),
          ...(isRowDisabled && { pointerEvents: "none" }),
        })}
      >
        <Typography component="span" variant="body1">
          {title}
        </Typography>
      </ListItemButton>
    </ListItem>
  )
}

export default SidebarItem
