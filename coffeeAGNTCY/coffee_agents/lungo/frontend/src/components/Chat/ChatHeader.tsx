/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
import UnfoldLess from "@mui/icons-material/UnfoldLess"
import UnfoldMore from "@mui/icons-material/UnfoldMore"
import type { Theme } from "@mui/material/styles"
import { Box, IconButton, Tooltip } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

/** OUK `Button` `variant="outlined"` look for header `IconButton`s. */
function chatHeaderIconButtonSx(theme: Theme) {
  return {
    width: 32,
    height: 32,
    minWidth: 32,
    padding: "6px",
    borderRadius: theme.shape.borderRadius,
    border: `2px solid ${theme.palette.vars.interactiveTertiaryDefault}`,
    background: "none",
    backgroundColor: "transparent",
    boxShadow: "none",
    ...iconGlyphFillSx(theme.palette.vars.controlIconDefault, {
      important: true,
    }),
    "&:hover": {
      border: `2px solid ${theme.palette.vars.interactiveTertiaryHover}`,
      background: "none",
      backgroundColor: "transparent",
    },
    "&:active": {
      border: `2px solid ${theme.palette.vars.interactiveTertiaryActive}`,
    },
  }
}

interface ChatHeaderProps {
  onMinimize?: () => void
  onClearConversation?: () => void
  isMinimized?: boolean
  /** ID of the expandable message panel controlled by the minimize button. */
  messagePanelId?: string
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onMinimize,
  onClearConversation,
  isMinimized = false,
  messagePanelId,
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "space-between",
        px: { xs: 1, sm: 2, md: 4, lg: 2 },
        py: 1,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center" }}>
        {onMinimize ? (
          <Tooltip title={isMinimized ? "Maximize" : "Minimize"}>
            <IconButton
              onClick={onMinimize}
              aria-label={isMinimized ? "Maximize" : "Minimize"}
              aria-expanded={!isMinimized}
              aria-controls={messagePanelId}
              sx={chatHeaderIconButtonSx}
            >
              {isMinimized ? (
                <UnfoldMore aria-hidden />
              ) : (
                <UnfoldLess aria-hidden />
              )}
            </IconButton>
          </Tooltip>
        ) : null}
      </Box>
      <Box sx={{ display: "flex", alignItems: "center" }}>
        {onClearConversation ? (
          <Tooltip title="Clear conversation">
            <IconButton
              onClick={onClearConversation}
              aria-label="Clear conversation"
              sx={chatHeaderIconButtonSx}
            >
              <DeleteOutline />
            </IconButton>
          </Tooltip>
        ) : null}
      </Box>
    </Box>
  )
}

export default ChatHeader
