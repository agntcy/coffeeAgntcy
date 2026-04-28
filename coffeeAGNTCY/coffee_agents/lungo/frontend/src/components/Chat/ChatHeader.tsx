/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Trash2 } from "lucide-react"
import {
  useThemeMode,
  Box,
  IconButton,
  Stack,
  Tooltip,
} from "@open-ui-kit/core"
import collapseIcon from "@/assets/collapse.png"

const collapseIconFilter = (isDarkMode: boolean) =>
  isDarkMode
    ? "brightness(0) saturate(100%) invert(85%) sepia(7%) saturate(398%) hue-rotate(186deg) brightness(97%) contrast(92%)"
    : "brightness(0) saturate(100%) invert(22%) sepia(8%) saturate(1157%) hue-rotate(192deg) brightness(95%) contrast(88%)"

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
  const { isDarkMode } = useThemeMode()

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
        borderBottom: "1px solid #23282e",
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        {onMinimize ? (
          <Tooltip title={isMinimized ? "Maximize" : "Minimize"}>
            <IconButton
              size="small"
              onClick={onMinimize}
              aria-label={isMinimized ? "Maximize" : "Minimize"}
              sx={{
                width: 28,
                height: 28,
                p: 0.5,
                borderRadius: 1,
              }}
            >
              <Box
                component="img"
                src={collapseIcon}
                alt=""
                sx={{
                  width: 20,
                  height: 20,
                  display: "block",
                  transform: isMinimized ? "rotate(180deg)" : "none",
                  filter: collapseIconFilter(isDarkMode),
                }}
              />
            </IconButton>
          </Tooltip>
        ) : null}
        {onClearConversation ? (
          <Tooltip title="Clear conversation">
            <IconButton
              size="small"
              onClick={onClearConversation}
              aria-label="Clear conversation"
              sx={{
                width: 28,
                height: 28,
                p: 0.5,
                borderRadius: 1,
              }}
            >
              <Trash2 size={20} aria-hidden />
            </IconButton>
          </Tooltip>
        ) : null}
      </Stack>
    </Box>
  )
}

export default ChatHeader
