/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef } from "react"
import { Box } from "@open-ui-kit/core"
import type { Message as MessageType } from "./types"
import Message from "./Message"

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
      {messages.map((msg: MessageType) => (
        <Message
          key={msg.id}
          content={msg.content}
          aiMessage={msg.role === "assistant"}
          animate={msg.animate}
          loading={false}
        />
      ))}

      <Box ref={messagesEndRef} />
    </Box>
  )
}

export default Messages
