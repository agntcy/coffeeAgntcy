/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

import { Stack, Typography } from "@open-ui-kit/core"
import Person from "@mui/icons-material/Person"

import { ChatAvatarCircle } from "./ChatAvatarCircle"

interface UserMessageProps {
  content: string
}

const UserMessage: React.FC<UserMessageProps> = ({ content }) => {
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={0.5}
      sx={{ width: "100%" }}
    >
      <ChatAvatarCircle>
        <Person sx={{ fontSize: 22 }} />
      </ChatAvatarCircle>

      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          alignItems: "flex-start",
          justifyContent: "center",
          borderRadius: 1,
          py: 0.5,
          px: 1,
        }}
      >
        <Typography
          variant="body2"
          component="div"
          sx={{
            whiteSpace: "pre-wrap",
            overflowWrap: "break-word",
            wordBreak: "break-word",
          }}
        >
          {content}
        </Typography>
      </Stack>
    </Stack>
  )
}

export default UserMessage
