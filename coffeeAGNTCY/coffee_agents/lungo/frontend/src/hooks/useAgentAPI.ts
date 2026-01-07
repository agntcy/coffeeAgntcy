/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef, useState, useEffect } from "react"
import axios from "axios"
import { v4 as uuid } from "uuid"
import { Message } from "@/types/message"
import { Role } from "@/utils/const"
import { withRetry, RETRY_CONFIG } from "@/utils/retryUtils"
import { shouldEnableRetries, getApiUrlForPattern } from "@/utils/patternUtils"

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
      onRetryAttempt?: (
        attempt: number,
        error: Error,
        nextRetryAt: number,
      ) => void
    },
    pattern?: string,
  ) => Promise<void>
  cancel: () => void
}

export const useAgentAPI = (): UseAgentAPIReturn => {
  const [loading, setLoading] = useState<boolean>(false)
  const abortRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef<number>(0)

  const cancel = () => {
    if (abortRef.current) {
      abortRef.current.abort()
    }
    requestIdRef.current += 1
  }

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [])

  const sendMessage = async (
    prompt: string,
    pattern?: string,
  ): Promise<string> => {
    if (!prompt.trim()) {
      throw new Error("Prompt cannot be empty")
    }

    const apiUrl = getApiUrlForPattern(pattern)

    setLoading(true)

    const controller = new AbortController()
    abortRef.current = controller
    const myRequestId = requestIdRef.current + 1
    requestIdRef.current = myRequestId

    const makeApiCall = async (): Promise<string> => {
      const response = await axios.post<ApiResponse>(
        `${apiUrl}/agent/prompt`,
        {
          prompt,
        },
        { signal: controller.signal, withCredentials: true },
      )
      return response.data.response
    }

    try {
      if (shouldEnableRetries(pattern)) {
        return await withRetry(makeApiCall)
      } else {
        return await makeApiCall()
      }
    } finally {
      if (requestIdRef.current === myRequestId) {
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
      onRetryAttempt?: (
        attempt: number,
        error: Error,
        nextRetryAt: number,
      ) => void
    },
    pattern?: string,
  ): Promise<void> => {
    if (!prompt.trim()) return

    const apiUrl = getApiUrlForPattern(pattern)

    const controller = new AbortController()
    abortRef.current = controller
    const myRequestId = requestIdRef.current + 1
    requestIdRef.current = myRequestId

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

    const makeApiCall = async (): Promise<string> => {
      const response = await axios.post<ApiResponse>(
        `${apiUrl}/agent/prompt`,
        {
          prompt,
        },
        { signal: controller.signal, withCredentials: true },
      )
      return response.data.response
    }

    const onRetryAttempt = (attempt: number) => {
      const delay =
        RETRY_CONFIG.baseDelay *
        Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1)
      const nextRetryAt = Date.now() + delay

      setMessages((prevMessages: Message[]) => {
        const updatedMessages = [...prevMessages]
        updatedMessages[updatedMessages.length - 1] = {
          role: "assistant",
          content: `Retrying... (${attempt}/${RETRY_CONFIG.maxRetries})`,
          id: uuid(),
          animate: true,
        }
        return updatedMessages
      })

      if (callbacks?.onRetryAttempt) {
        callbacks.onRetryAttempt(
          attempt,
          new Error("Retry attempt"),
          nextRetryAt,
        )
      }
    }

    try {
      let responseText: string

      if (shouldEnableRetries(pattern)) {
        responseText = await withRetry(makeApiCall, onRetryAttempt)
      } else {
        responseText = await makeApiCall()
      }

      if (requestIdRef.current === myRequestId) {
        setMessages((prevMessages: Message[]) => {
          const updatedMessages = [...prevMessages]
          updatedMessages[updatedMessages.length - 1] = {
            role: "assistant",
            content: responseText,
            id: uuid(),
            animate: true,
          }
          return updatedMessages
        })
      }

      if (callbacks?.onSuccess) {
        callbacks.onSuccess(responseText)
      }
    } catch (error) {
      if (requestIdRef.current === myRequestId) {
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
      }

      if (callbacks?.onError) {
        callbacks.onError(error)
      }
    } finally {
      if (requestIdRef.current === myRequestId) {
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
