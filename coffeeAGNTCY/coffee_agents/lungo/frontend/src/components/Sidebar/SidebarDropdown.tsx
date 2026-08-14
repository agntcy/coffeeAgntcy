/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import {
  Box,
  IconButton,
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
  sidebarRowTitleSx,
} from "./sidebarSx"

interface SidebarDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  /** When set, the title opens a page; the chevron alone expands/collapses children. */
  onTitleClick?: () => void
  isTitleSelected?: boolean
  children: React.ReactNode
}

const SidebarDropdown: React.FC<SidebarDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  onTitleClick,
  isTitleSelected = false,
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

  const handleTitleClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    onTitleClick?.()
  }

  const chevron = (
    <ExpandLess
      sx={{
        transition: "transform 150ms ease",
        transform: isExpanded ? "rotate(0deg)" : "rotate(180deg)",
      }}
    />
  )

  const titleTypography = (
    <Typography
      id={titleId}
      component="span"
      variant="body1"
      sx={{
        flex: "1 1 auto",
        ...sidebarRowTitleSx,
      }}
    >
      {title}
    </Typography>
  )

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
      {onTitleClick ? (
        <Box
          sx={{
            display: "flex",
            width: "100%",
            minWidth: 0,
            alignItems: "center",
            gap: 0.5,
          }}
        >
          <ListItemButton
            component="button"
            onClick={handleTitleClick}
            selected={isTitleSelected}
            aria-current={isTitleSelected ? "page" : undefined}
            sx={(theme) => ({
              ...sidebarListItemButtonSx,
              ...sidebarRowButtonStateSx(theme),
              flex: "1 1 auto",
              minWidth: 0,
              alignItems: "center",
              justifyContent: "flex-start",
              borderRadius: sidebarBorderRadius,
              textWrap: "wrap",
            })}
          >
            {titleTypography}
          </ListItemButton>
          <IconButton
            id={toggleId}
            onClick={handleToggle}
            aria-expanded={isExpanded}
            aria-controls={panelId}
            aria-label={toggleLabel}
            sx={(theme) => ({
              ...sidebarRowButtonStateSx(theme),
              flex: "none",
              alignSelf: "center",
              borderRadius: sidebarBorderRadius,
            })}
          >
            {chevron}
          </IconButton>
        </Box>
      ) : (
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
            alignItems: "center",
            justifyContent: "space-between",
            borderRadius: sidebarBorderRadius,
            textWrap: "wrap",
          })}
        >
          {titleTypography}
          <Box
            component="span"
            aria-hidden
            sx={{
              flex: "none",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              alignSelf: "center",
              p: 0.25,
            }}
          >
            {chevron}
          </Box>
        </ListItemButton>
      )}

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
