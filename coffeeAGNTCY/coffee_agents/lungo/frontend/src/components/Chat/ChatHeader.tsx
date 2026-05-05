/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { IconButton } from "@open-ui-kit/core"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
import Box from "@mui/material/Box"
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
    <div
      className="flex w-full items-center justify-end px-2 py-2 sm:px-4 md:px-8 lg:px-4"
      style={{ borderBottom: "1px solid var(--control-border-weak)" }}
    >
      <div className="flex items-center gap-2">
        {onMinimize && (
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
        )}
        {onClearConversation && (
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
            <DeleteOutline sx={{ fontSize: 20 }} />
          </IconButton>
        )}
      </div>
    </div>
  )
}

export default ChatHeader
