/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, IconButton, Icons, Tooltip } from "@open-ui-kit/core"

import { chatHeaderIconButtonSx } from "./chatHeaderIconButtonSx"
import {
  mainAreaContentHorizontalPadding,
  type MainAreaContentHorizontalPadding,
} from "@/components/MainArea/mainAreaContentPadding"

interface ChatHeaderProps {
  onClearConversation?: () => void
  horizontalPadding?: MainAreaContentHorizontalPadding
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onClearConversation,
  horizontalPadding = mainAreaContentHorizontalPadding,
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
            size="small"
            onClick={onClearConversation}
            aria-label="Clear conversation"
            sx={chatHeaderIconButtonSx}
          >
            <Icons.Delete />
          </IconButton>
        </Tooltip>
      ) : null}
    </Box>
  )
}

export default ChatHeader
