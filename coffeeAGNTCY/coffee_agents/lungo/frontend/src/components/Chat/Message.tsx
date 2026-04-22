/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useState } from "react"
import { Box, Stack, Typography } from "@open-ui-kit/core"
import { HiUser } from "react-icons/hi"
import { RiRobot2Fill } from "react-icons/ri"
import { Waveform } from "ldrs/react"
import "ldrs/react/Waveform.css"

interface SlowTextProps {
  text: string
  speed?: number
}

const SlowText: React.FC<SlowTextProps> = ({ text, speed = 25 }) => {
  const [displayedText, setDisplayedText] = useState<string>("")
  const idx = useRef<number>(-1)

  useEffect(() => {
    function tick(): void {
      idx.current++
      setDisplayedText((prev: string) => prev + text[idx.current])
    }

    if (idx.current < text.length - 1) {
      const addChar = setInterval(tick, speed)
      return () => clearInterval(addChar)
    }
  }, [displayedText, speed, text])

  return <span>{displayedText}</span>
}

interface MessageProps {
  content: string
  aiMessage: boolean
  animate: boolean
  loading: boolean
}

const Message: React.FC<MessageProps> = ({
  content,
  aiMessage,
  animate,
  loading,
}) => {
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={2}
      sx={{
        width: "100%",
        px: { xs: 2, sm: 4, md: 8, lg: 15 },
        py: { xs: 3, md: 3.75 },
        bgcolor: aiMessage ? "rgb(247, 247, 248)" : "transparent",
      }}
    >
      <Box
        sx={{
          width: 35,
          height: 35,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {aiMessage ? <RiRobot2Fill color="#049FD9" /> : <HiUser />}
      </Box>
      <Box
        sx={{
          minWidth: 0,
          flex: 1,
          overflowWrap: "break-word",
          wordBreak: "break-word",
        }}
      >
        {loading ? (
          <Box sx={{ opacity: 0.5 }}>
            <Waveform size="20" stroke="3.5" speed="1" color="#049FD9" />
          </Box>
        ) : (
          <Typography
            variant="body2"
            component="div"
            sx={{
              whiteSpace: "pre-wrap",
              overflowWrap: "break-word",
              wordBreak: "break-word",
            }}
          >
            {animate ? <SlowText speed={20} text={content} /> : content}
          </Typography>
        )}
      </Box>
    </Stack>
  )
}

export default Message
