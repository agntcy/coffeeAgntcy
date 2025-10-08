/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import axios from "axios"
import { v4 as uuid } from "uuid"
import { Message } from "@/types/message"
import { Role } from "@/utils/const"

const DEFAULT_PUB_SUB_API_URL = "http://127.0.0.1:8000"
const DEFAULT_GROUP_COMM_APP_API_URL = "http://127.0.0.1:9090"
const PUB_SUB_APP_API_URL =
  import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_PUB_SUB_API_URL
const GROUP_COMM_APP_API_URL =
  import.meta.env.VITE_LOGISTICS_APP_API_URL || DEFAULT_GROUP_COMM_APP_API_URL

interface ApiResponse {
  response: string
}

interface UseAgentAPIReturn {
  loading: boolean
  sendMessage: (prompt: string, pattern?: string) => Promise<string>
  sendMessageWithCallback: (
    prompt: string,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    callbacks?: {
      onStart?: () => void
      onSuccess?: (response: string) => void
      onError?: (error: any) => void
    },
    pattern?: string,
  ) => Promise<void>
}

export const useAgentAPI = (): UseAgentAPIReturn => {
  const [loading, setLoading] = useState<boolean>(false)

  const sendMessage = async (
    prompt: string,
    pattern?: string,
  ): Promise<string> => {
    if (!prompt.trim()) {
      throw new Error("Prompt cannot be empty")
    }

    const apiUrl =
      pattern === "group_communication"
        ? GROUP_COMM_APP_API_URL
        : PUB_SUB_APP_API_URL

    setLoading(true)
    try {
      const response = await axios.post<ApiResponse>(`${apiUrl}/agent/prompt`, {
        prompt,
      })
      return response.data.response
    } finally {
      setLoading(false)
    }
  }

  const sendMessageWithCallback = async (
    prompt: string,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    callbacks?: {
      onStart?: () => void
      onSuccess?: (response: string) => void
      onError?: (error: any) => void
    },
    pattern?: string,
  ): Promise<void> => {
    if (!prompt.trim()) return

    const apiUrl =
      pattern === "group_communication"
        ? GROUP_COMM_APP_API_URL
        : PUB_SUB_APP_API_URL

    const userMessage: Message = {
      role: Role.USER,
      content: prompt,
      id: uuid(),
      animate: false,
    }

    const loadingMessage: Message = {
      role: "assistant",
      content: "...",
      id: uuid(),
      animate: true,
    }

    setMessages((prevMessages: Message[]) => [
      ...prevMessages,
      userMessage,
      loadingMessage,
    ])
    setLoading(true)

    if (callbacks?.onStart) {
      callbacks.onStart()
    }

    try {
      const response = await axios.post<ApiResponse>(`${apiUrl}/agent/prompt`, {
        prompt,
      })

      setMessages((prevMessages: Message[]) => {
        const updatedMessages = [...prevMessages]
        updatedMessages[updatedMessages.length - 1] = {
          role: "assistant",
          content: response.data.response,
          id: uuid(),
          animate: true,
        }
        return updatedMessages
      })

      if (callbacks?.onSuccess) {
        callbacks.onSuccess(response.data.response)
      }
    } catch (error) {
      setMessages((prevMessages: Message[]) => {
        const updatedMessages = [...prevMessages]
        updatedMessages[updatedMessages.length - 1] = {
          role: "assistant",
          content: "Sorry, I encountered an error.",
          id: uuid(),
          animate: false,
        }
        return updatedMessages
      })

      if (callbacks?.onError) {
        callbacks.onError(error)
      }
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    sendMessage,
    sendMessageWithCallback,
  }
}
