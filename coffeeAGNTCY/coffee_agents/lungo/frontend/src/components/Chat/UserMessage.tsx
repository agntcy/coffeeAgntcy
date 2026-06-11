/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import Person from "@mui/icons-material/Person"
import { useTheme } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

import { ChatAvatarCircle } from "./ChatAvatarCircle"
import Message from "./Message"

interface UserMessageProps {
  content: string
}

const UserMessage: React.FC<UserMessageProps> = ({ content }) => {
  const theme = useTheme()
  const avatarIconColor = theme.palette.grey[50]

  return (
    <Message
      icon={
        <ChatAvatarCircle>
          <Person sx={iconGlyphFillSx(avatarIconColor, { important: true })} />
        </ChatAvatarCircle>
      }
    >
      {content}
    </Message>
  )
}

export default UserMessage
