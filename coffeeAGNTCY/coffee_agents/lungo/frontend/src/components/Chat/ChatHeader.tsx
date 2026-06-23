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

function chatHeaderIconButtonSx(theme: Theme) {
  return {
    width: 32,
    height: 32,
    minWidth: 32,
    padding: "6px",
    borderRadius: theme.shape.borderRadius,
    background: "none",
    backgroundColor: "transparent",
    boxShadow: "none",
    ...iconGlyphFillSx(theme.palette.vars.controlIconDefault, {
      important: true,
    }),
  }
}

interface ChatHeaderProps {
  onMinimize?: () => void
  onClearConversation?: () => void
  isMinimized?: boolean
  /** ID of the expandable message panel controlled by the minimize button. */
  messagePanelId?: string
  horizontalPadding?: { xs: number; sm: number; md: number; lg: number }
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onMinimize,
  onClearConversation,
  isMinimized = false,
  messagePanelId,
  horizontalPadding = { xs: 2, sm: 4, md: 8, lg: 15 },
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "space-between",
        px: horizontalPadding,
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
