/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef, useState, useEffect } from "react"
import { v4 as uuid } from "uuid"
import { fetchJson, isHttpError } from "@/api/http"
import type { Message } from "@/components/Chat/types"
import { reportRequestError } from "@/errors/request"
import { isLocalDev, Role } from "@/utils/const"
import { withRetry, RETRY_CONFIG } from "@/utils/retryUtils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  getAgentPromptRequestForWorkflow,
  shouldEnableRetriesForWorkflow,
} from "@/utils/workflow"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"
import type { ApiResponse } from "@/types/api"

/** Builds the non-streaming /agent/prompt body, tagging it with the active
 *  workflow instance id (when present) so the backend emits workflow events on
 *  the same instance the events SSE listener is subscribed under. Without this
 *  the backend mints a throwaway instance id, its events 404 on the internal
 *  events endpoint, and graph animations never render in non-streaming mode. */
export const buildPromptRequestBody = (
  prompt: string,
): { prompt: string; workflow_instance_id?: string } => {
  const workflowInstanceId =
    useActiveWorkflowInstanceStore.getState().workflowInstanceId
  return {
    prompt,
    ...(workflowInstanceId ? { workflow_instance_id: workflowInstanceId } : {}),
  }
}

function rethrowAgentPromptError(error: unknown): never {
  if (isHttpError(error)) {
    if (
      error.status !== undefined &&
      error.status >= 400 &&
      error.status < 500
    ) {
      throw new Error(`HTTP ${error.status} - ${error.message}`)
    }
    throw new Error(error.message)
  }

  throw error instanceof Error ? error : new Error(String(error))
}

interface UseAgentAPIReturn {
  loading: boolean
  sendMessage: (
    prompt: string,
    summary?: WorkflowSummary | null,
  ) => Promise<ApiResponse>
  sendMessageWithCallback: (
    prompt: string,
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
    callbacks?: {
      onStart?: () => void
      onSuccess?: (response: ApiResponse) => void
      onError?: (error: Error) => void
      onRetryAttempt?: (
        attempt: number,
        error: Error,
        nextRetryAt: number,
      ) => void
    },
    summary?: WorkflowSummary | null,
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
    summary?: WorkflowSummary | null,
  ): Promise<ApiResponse> => {
    if (!prompt.trim()) {
      throw new Error("Prompt cannot be empty")
    }

    const promptRequest = getAgentPromptRequestForWorkflow(summary)
    setLoading(true)

    const controller = new AbortController()
    abortRef.current = controller
    const myRequestId = requestIdRef.current + 1
    requestIdRef.current = myRequestId

    const makeApiCall = async (): Promise<ApiResponse> =>
      fetchJson<ApiResponse>(promptRequest.url, {
        method: "POST",
        body: JSON.stringify(buildPromptRequestBody(prompt)),
        credentials: isLocalDev ? "omit" : "include",
        signal: controller.signal,
        endpointLabel: promptRequest.endpointLabel,
      })

    try {
      if (shouldEnableRetriesForWorkflow(summary)) {
        return await withRetry(makeApiCall)
      }
      return await makeApiCall()
    } catch (error) {
      reportRequestError(promptRequest.endpointLabel, error)
      rethrowAgentPromptError(error)
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
      onSuccess?: (response: ApiResponse) => void
      onError?: (error: Error) => void
      onRetryAttempt?: (
        attempt: number,
        error: Error,
        nextRetryAt: number,
      ) => void
    },
    summary?: WorkflowSummary | null,
  ): Promise<void> => {
    if (!prompt.trim()) return

    const promptRequest = getAgentPromptRequestForWorkflow(summary)
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

    const makeApiCall = async (): Promise<ApiResponse> =>
      fetchJson<ApiResponse>(promptRequest.url, {
        method: "POST",
        body: JSON.stringify(buildPromptRequestBody(prompt)),
        credentials: isLocalDev ? "omit" : "include",
        signal: controller.signal,
        endpointLabel: promptRequest.endpointLabel,
      })

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
      let apiResponse: ApiResponse

      if (shouldEnableRetriesForWorkflow(summary)) {
        apiResponse = await withRetry(makeApiCall, onRetryAttempt)
      } else {
        apiResponse = await makeApiCall()
      }

      if (requestIdRef.current === myRequestId) {
        setMessages((prevMessages: Message[]) => {
          const updatedMessages = [...prevMessages]
          updatedMessages[updatedMessages.length - 1] = {
            role: "assistant",
            content: apiResponse.response,
            id: uuid(),
            animate: true,
          }
          return updatedMessages
        })
      }

      if (callbacks?.onSuccess) {
        callbacks.onSuccess(apiResponse)
      }
    } catch (error) {
      reportRequestError(promptRequest.endpointLabel, error)

      let userMessage: string
      if (isHttpError(error)) {
        userMessage =
          error.status !== undefined &&
          error.status >= 400 &&
          error.status < 500
            ? `HTTP ${error.status} - ${error.message}`
            : error.message
      } else {
        userMessage = error instanceof Error ? error.message : String(error)
      }

      if (requestIdRef.current === myRequestId) {
        setMessages((prevMessages: Message[]) => {
          const updatedMessages = [...prevMessages]
          updatedMessages[updatedMessages.length - 1] = {
            role: "assistant",
            content: userMessage,
            id: uuid(),
            animate: false,
          }
          return updatedMessages
        })
      }

      if (callbacks?.onError) {
        callbacks.onError(
          error instanceof Error ? error : new Error(userMessage),
        )
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
