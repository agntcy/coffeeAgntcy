/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
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
  onClearConversation?: () => void
  horizontalPadding?: { xs: number; sm: number; md: number; lg: number }
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onClearConversation,
  horizontalPadding = { xs: 2, sm: 4, md: 8, lg: 15 },
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "flex-end",
        px: horizontalPadding,
        py: 1,
      }}
    >
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
  )
}

export default ChatHeader
