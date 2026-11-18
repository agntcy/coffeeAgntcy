/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, IconButton, Icons, Stack, Tooltip } from "@open-ui-kit/core"
import { chatHeaderIconButtonSx } from "./header/chatHeaderIconButtonSx"

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
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Stack direction="row" spacing={1}>
        {onMinimize && (
          <Tooltip title={isMinimized ? "Maximize" : "Minimize"}>
            <IconButton
              onClick={onMinimize}
              aria-label={isMinimized ? "Maximize" : "Minimize"}
              sx={chatHeaderIconButtonSx}
            >
              <Icons.KeyboardArrowDown
                sx={{
                  transition: (theme) =>
                    theme.transitions.create("transform", {
                      duration: theme.transitions.duration.shortest,
                    }),
                  transform: isMinimized ? "rotate(180deg)" : "rotate(0deg)",
                }}
              />
            </IconButton>
          </Tooltip>
        )}
        {onClearConversation && (
          <Tooltip title="Clear conversation">
            <IconButton
              onClick={onClearConversation}
              aria-label="Clear conversation"
              sx={chatHeaderIconButtonSx}
            >
              <Icons.Delete />
            </IconButton>
          </Tooltip>
        )}
      </Stack>
    </Box>
  )
}

export default ChatHeader
