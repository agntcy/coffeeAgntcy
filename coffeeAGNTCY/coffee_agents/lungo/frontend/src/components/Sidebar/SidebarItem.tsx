/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined"
import {
  IconButton,
  ListItem,
  ListItemButton,
  Tooltip,
  Typography,
} from "@open-ui-kit/core"
import { openWorkflowDocumentationInNewTab } from "@/utils/workflowDocumentationGithub"
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
  documentationCatalogName?: string
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  isSelected = false,
  onClick,
  disabled = false,
  documentationCatalogName,
}) => {
  const isRowDisabled = disabled || onClick === undefined
  const hasDocumentationAction = documentationCatalogName !== undefined

  const handleDocumentationClick = () => {
    openWorkflowDocumentationInNewTab(documentationCatalogName!)
  }

  return (
    <ListItem
      component="div"
      disablePadding
      sx={(theme) => ({
        width: "100%",
        display: "flex",
        alignItems: "center",
        gap: 0.5,
        mt: sidebarItemMarginTop,
        ...sidebarListItemSx(theme),
      })}
    >
      <ListItemButton
        component={!isRowDisabled ? "button" : "div"}
        type={!isRowDisabled ? "button" : undefined}
        disabled={isRowDisabled && !hasDocumentationAction}
        onClick={!disabled ? onClick : undefined}
        selected={isSelected}
        sx={{
          ...sidebarListItemButtonSx,
          flex: 1,
          minWidth: 0,
          justifyContent: "flex-start",
          borderRadius: sidebarBorderRadius,
          textWrap: "auto",
          ...(disabled && { opacity: 0.5 }),
          ...(isRowDisabled &&
            !hasDocumentationAction && { pointerEvents: "none" }),
        }}
      >
        <Typography component="span" variant="body1">
          {title}
        </Typography>
      </ListItemButton>
      {hasDocumentationAction ? (
        <Tooltip title="View documentation on GitHub">
          <IconButton
            size="small"
            aria-label={`Open documentation for ${documentationCatalogName}`}
            onClick={handleDocumentationClick}
            sx={{ flexShrink: 0, p: 0.625 }}
          >
            <DescriptionOutlinedIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ) : null}
    </ListItem>
  )
}

export default SidebarItem
