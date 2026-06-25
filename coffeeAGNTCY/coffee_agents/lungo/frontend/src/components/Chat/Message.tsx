/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import type { SystemStyleObject } from "@mui/system"
import type { Theme } from "@mui/material/styles"

const messageBodyTypographySx: SystemStyleObject<Theme> = {
  whiteSpace: "pre-wrap",
  overflowWrap: "break-word",
  wordBreak: "break-word",
  py: 1,
}

export interface MessageProps {
  /** Leading avatar or icon for the row. */
  icon: React.ReactNode
  /** Message body; wrapped in shared chat-area `body1` typography styles. */
  children: React.ReactNode
  /** Assistant / highlighted rows use `action.hover` background. */
  highlighted?: boolean
}

const Message: React.FC<MessageProps> = ({
  icon,
  children,
  highlighted = false,
}) => {
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={2}
      sx={{
        width: "100%",
        bgcolor: highlighted ? "action.hover" : "transparent",
      }}
    >
      <Box
        sx={{
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </Box>
      <Box
        sx={{
          minWidth: 0,
          flex: 1,
          overflowWrap: "break-word",
          wordBreak: "break-word",
        }}
      >
        <Typography
          variant="body1"
          component="div"
          sx={messageBodyTypographySx}
        >
          {children}
        </Typography>
      </Box>
    </Stack>
  )
}

export default Message
