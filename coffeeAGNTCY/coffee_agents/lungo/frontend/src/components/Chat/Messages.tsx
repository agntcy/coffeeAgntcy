/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useState } from "react"
import Person from "@mui/icons-material/Person"
import SmartToy from "@mui/icons-material/SmartToy"
import { Box } from "@open-ui-kit/core"
import type { Message as MessageType } from "./types"
import Message from "./Message"

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

export const LOCAL_STORAGE_KEY = "chat_messages"

interface MessagesProps {
  messages: MessageType[]
}

const Messages: React.FC<MessagesProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <Box>
      {messages.map((msg: MessageType) => {
        const isAssistant = msg.role === "assistant"

        return (
          <Message
            key={msg.id}
            highlighted={isAssistant}
            icon={isAssistant ? <SmartToy /> : <Person />}
          >
            {msg.animate ? (
              <SlowText speed={20} text={msg.content} />
            ) : (
              msg.content
            )}
          </Message>
        )
      })}

      <Box ref={messagesEndRef} />
    </Box>
  )
}

export default Messages
