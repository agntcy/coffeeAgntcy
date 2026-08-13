/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DeleteOutline from "@mui/icons-material/DeleteOutline"
import { Box, IconButton, Tooltip } from "@open-ui-kit/core"

import { chatHeaderIconButtonSx } from "./chatHeaderIconButtonSx"

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
