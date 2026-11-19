/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback, useEffect, useRef, useState } from "react"
import axios from "axios"
import { v4 as uuid } from "uuid"
import { Role } from "@/utils/const"
import { Message } from "@/types/Message"
import { env } from "@/utils/env"

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  env.get("VITE_EXCHANGE_APP_API_URL") ?? DEFAULT_EXCHANGE_APP_API_URL

interface ApiResponse {
  response: string
}

interface UseAgentAPIReturn {
  loading: boolean
  sendMessage: (prompt: string) => Promise<string | undefined>
  sendMessageWithCallback: (
    prompt: string,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    callbacks?: {
      onStart?: () => void
      onSuccess?: (response: string) => void
      onError?: (error: any) => void
    },
  ) => Promise<void>
  cancel: () => void
}

export const useAgentAPI = (): UseAgentAPIReturn => {
  const [loading, setLoading] = useState<boolean>(false)
  const abortRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    requestIdRef.current += 1
    setLoading(false)
  }, [])

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const beginRequest = () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setLoading(true)
    return { controller, requestId }
  }

  const isCurrent = (requestId: number) => requestIdRef.current === requestId

  const sendMessage = async (prompt: string): Promise<string | undefined> => {
    if (!prompt.trim()) {
      throw new Error("Prompt cannot be empty")
    }

    const { controller, requestId } = beginRequest()
    try {
      const response = await axios.post<ApiResponse>(
        `${EXCHANGE_APP_API_URL}/agent/prompt`,
        {
          prompt,
        },
        { signal: controller.signal },
      )
      if (!isCurrent(requestId)) return
      return response.data.response
    } catch (error) {
      if (controller.signal.aborted || !isCurrent(requestId)) return
      throw error
    } finally {
      if (isCurrent(requestId)) {
        setLoading(false)
      }
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
  ): Promise<void> => {
    if (!prompt.trim()) return

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

    const { controller, requestId } = beginRequest()

    setMessages((prevMessages: Message[]) => [
      ...prevMessages,
      userMessage,
      loadingMessage,
    ])

    if (callbacks?.onStart) {
      callbacks.onStart()
    }

    try {
      const response = await axios.post<ApiResponse>(
        `${EXCHANGE_APP_API_URL}/agent/prompt`,
        {
          prompt,
        },
        { signal: controller.signal },
      )

      if (!isCurrent(requestId)) return

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
      if (controller.signal.aborted || !isCurrent(requestId)) return

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
      if (isCurrent(requestId)) {
        setLoading(false)
      }
    }
  }

  return {
    loading,
    sendMessage,
    sendMessageWithCallback,
    cancel,
  }
}
