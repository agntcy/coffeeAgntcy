/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { useTheme, useThemeMode, Box } from "@open-ui-kit/core"

import AgentIcon from "@/assets/Coffee_Icon.svg"

export interface ChatAvatarCircleProps {
  children: React.ReactNode
}

export const ChatAvatarCircle: React.FC<ChatAvatarCircleProps> = ({
  children,
}) => {
  const { isDarkMode } = useThemeMode()
  const theme = useTheme()
  const avatarBg = isDarkMode
    ? theme.palette.vars.agentcyDarkBlue
    : theme.palette.vars.agentcyBlue

  return (
    <Box
      sx={{
        width: 40,
        height: 40,
        flexShrink: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: "50%",
        bgcolor: avatarBg,
      }}
    >
      {children}
    </Box>
  )
}

export const ChatAgentAvatar: React.FC = () => {
  const theme = useTheme()

  return (
    <ChatAvatarCircle>
      <Box
        role="img"
        aria-label="Agent"
        sx={{
          width: 22,
          height: 22,
          flexShrink: 0,
          bgcolor: theme.palette.grey[50],
          maskImage: `url(${AgentIcon})`,
          maskSize: "contain",
          maskRepeat: "no-repeat",
          maskPosition: "center",
          WebkitMaskImage: `url(${AgentIcon})`,
          WebkitMaskSize: "contain",
          WebkitMaskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
        }}
      />
    </ChatAvatarCircle>
  )
}

export default ChatAvatarCircle
