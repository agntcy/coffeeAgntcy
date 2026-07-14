/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  Typography,
} from "@open-ui-kit/core"
import ExpandLess from "@mui/icons-material/ExpandLess"
import {
  sidebarBorderRadius,
  sidebarDropdownPanelPaddingLeft,
  sidebarItemMarginTop,
  sidebarListItemButtonSx,
  sidebarListItemSx,
  sidebarRowButtonStateSx,
} from "./sidebarSx"

interface SidebarDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  const toggleId = React.useId()
  const titleId = React.useId()
  const panelId = React.useId()
  const toggleLabel = `${isExpanded ? "Collapse" : "Expand"} ${title}`

  const handleToggle = (event: React.MouseEvent) => {
    event.stopPropagation()
    onToggle()
  }

  return (
    <ListItem
      component="div"
      disablePadding
      sx={() => ({
        width: "100%",
        flexDirection: "column",
        alignItems: "stretch",
        mt: sidebarItemMarginTop,
        ...sidebarListItemSx(),
      })}
    >
      <ListItemButton
        component="button"
        id={toggleId}
        onClick={handleToggle}
        aria-expanded={isExpanded}
        aria-controls={panelId}
        aria-label={toggleLabel}
        sx={(theme) => ({
          ...sidebarListItemButtonSx,
          ...sidebarRowButtonStateSx(theme),
          width: "100%",
          minWidth: 0,
          justifyContent: "space-between",
          borderRadius: sidebarBorderRadius,
          textWrap: "auto",
        })}
      >
        <Typography id={titleId} component="span" variant="body1">
          {title}
        </Typography>
        <Box
          component="span"
          aria-hidden
          sx={{
            flex: "none",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            p: 0.25,
          }}
        >
          <ExpandLess
            sx={{
              transition: "transform 150ms ease",
              transform: isExpanded ? "rotate(0deg)" : "rotate(180deg)",
            }}
          />
        </Box>
      </ListItemButton>

      {isExpanded ? (
        <List
          component="div"
          disablePadding
          id={panelId}
          role="region"
          aria-labelledby={titleId}
          sx={(theme) => ({
            width: "100%",
            pl: sidebarDropdownPanelPaddingLeft(theme),
          })}
        >
          {children}
        </List>
      ) : null}
    </ListItem>
  )
}

export default SidebarDropdown
