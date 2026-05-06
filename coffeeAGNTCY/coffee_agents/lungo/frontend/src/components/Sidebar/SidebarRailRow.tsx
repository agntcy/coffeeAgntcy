/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Leaf row for the sidebar rail — same layout as `renderListItem` in SidebarFrame (icon + label
 * with opacity when `railOpen` is false, tooltip when collapsed).
 *
 **/

import React from "react"
import { ListItemIcon, ListItemText } from "@mui/material"
import {
  Link,
  ListItem,
  ListItemButton,
  Stack,
  Tooltip,
} from "@open-ui-kit/core"
import { sidebarBorderRadius, sidebarItemMt } from "./sidebarSx"

export interface SidebarRailRowProps {
  id: string
  "aria-label": string
  /** Shown as ListItemText and as Tooltip title. */
  tooltip: string
  icon?: React.ReactElement
  /**
   * When the drawer is wide enough to show labels: `true` shows primary text and disables hover tooltips.
   * When `false` (collapsed rail), label fades out and tooltips show on hover — same as `renderListItem`.
   */
  railOpen: boolean
  onClick?: () => void
  href?: string
  target?: string
  selected?: boolean
}

export function SidebarRailRow({
  id,
  "aria-label": ariaLabel,
  tooltip,
  icon,
  railOpen,
  onClick,
  href,
  target,
  selected = false,
}: SidebarRailRowProps) {
  const label = (
    <Stack
      direction="row"
      alignItems="center"
      justifyContent="center"
      sx={{
        width: "100%",
        p: 0.5,
        pl: railOpen ? 2 : 0.5,
      }}
    >
      <ListItemIcon
        sx={{
          minWidth: 0,
          justifyContent: "center",
          mr: railOpen ? 1 : 0,
        }}
      >
        {icon}
      </ListItemIcon>
      <ListItemText
        primary={tooltip}
        sx={{
          ml: 0.5,
          display: railOpen ? "block" : "none",
          textWrap: "auto",
        }}
      />
    </Stack>
  )

  const tooltipChild = (
    <Tooltip
      title={tooltip || ""}
      placement="right"
      disableHoverListener={railOpen}
    >
      {label}
    </Tooltip>
  )

  if (href) {
    return (
      <ListItem
        key={id}
        disablePadding
        sx={{
          backgroundColor: "transparent",
          mt: sidebarItemMt,
        }}
      >
        <ListItemButton
          aria-label={ariaLabel}
          component={Link}
          href={href}
          target={target}
          rel={target === "_blank" ? "noopener noreferrer" : undefined}
          sx={{
            color: "inherit",
            backgroundColor: "transparent",
            textDecoration: "none",
            borderRadius: sidebarBorderRadius,
            p: 0.5,
            pl: 2,
          }}
        >
          {tooltipChild}
        </ListItemButton>
      </ListItem>
    )
  }

  if (onClick) {
    return (
      <ListItem
        key={id}
        disablePadding
        sx={{
          backgroundColor: "transparent",
          borderRadius: sidebarBorderRadius,
          mt: sidebarItemMt,
        }}
      >
        <ListItemButton
          selected={selected}
          onClick={onClick}
          aria-label={ariaLabel}
          sx={{
            backgroundColor: "transparent",
            borderRadius: sidebarBorderRadius,
            p: 0,
          }}
        >
          {tooltipChild}
        </ListItemButton>
      </ListItem>
    )
  }

  return (
    <ListItem
      key={id}
      sx={{
        backgroundColor: "transparent",
        mt: sidebarItemMt,
      }}
    >
      {tooltipChild}
    </ListItem>
  )
}
