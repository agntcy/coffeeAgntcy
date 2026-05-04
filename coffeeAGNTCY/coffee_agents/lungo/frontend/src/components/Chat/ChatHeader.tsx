/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
import { Box, IconButton, Stack, Tooltip } from "@open-ui-kit/core"
import collapseIcon from "@/assets/collapse.png"

interface ChatHeaderProps {
  onMinimize?: () => void
  onClearConversation?: () => void
  isMinimized?: boolean
  showActions?: boolean
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onMinimize,
  onClearConversation,
  isMinimized,
  showActions = false,
}) => {
  if (!showActions) {
    return null
  }

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "flex-end",
        px: { xs: 1, sm: 2, md: 4, lg: 2 },
        py: 1,
        borderBottom: 1,
        borderColor: "divider",
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        {onMinimize ? (
          <Tooltip title={isMinimized ? "Maximize" : "Minimize"}>
            <IconButton
              onClick={onMinimize}
              size="small"
              color="inherit"
              aria-label={isMinimized ? "Maximize" : "Minimize"}
              title={isMinimized ? "Maximize" : "Minimize"}
              sx={{
                width: 28,
                height: 28,
                p: 0.5,
              }}
            >
              <Box
                component="img"
                src={collapseIcon}
                alt=""
                className="chat-header-icon"
                sx={{
                  width: 20,
                  height: 20,
                  transform: isMinimized ? "rotate(180deg)" : undefined,
                  bgcolor: "#ffffff",
                }}
              />
            </IconButton>
          </Tooltip>
        ) : null}
        {onClearConversation ? (
          <Tooltip title="Clear conversation">
            <IconButton
              onClick={onClearConversation}
              size="small"
              color="inherit"
              aria-label="Clear conversation"
              title="Clear conversation"
              sx={{
                width: 28,
                height: 28,
                p: 0.5,
              }}
            >
              <DeleteOutline />
            </IconButton>
          </Tooltip>
        ) : null}
      </Stack>
    </Box>
  )
}

export default ChatHeader
