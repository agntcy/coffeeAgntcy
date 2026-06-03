/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
import UnfoldLess from "@mui/icons-material/UnfoldLess"
import UnfoldMore from "@mui/icons-material/UnfoldMore"
import { Box, IconButton, Stack, Tooltip } from "@open-ui-kit/core"

interface ChatHeaderProps {
  onMinimize?: () => void
  onClearConversation?: () => void
  isMinimized?: boolean
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onMinimize,
  onClearConversation,
  isMinimized,
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        alignItems: "center",
        justifyContent: "flex-end",
        px: { xs: 1, sm: 2, md: 4, lg: 2 },
        py: 1,
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        {onMinimize ? (
          <Tooltip title={isMinimized ? "Maximize" : "Minimize"}>
            <IconButton
              onClick={onMinimize}
              color="inherit"
              aria-label={isMinimized ? "Maximize" : "Minimize"}
            >
              {isMinimized ? (
                <UnfoldMore aria-hidden />
              ) : (
                <UnfoldLess aria-hidden />
              )}
            </IconButton>
          </Tooltip>
        ) : null}
        {onClearConversation ? (
          <Tooltip title="Clear conversation">
            <IconButton
              onClick={onClearConversation}
              color="inherit"
              aria-label="Clear conversation"
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
