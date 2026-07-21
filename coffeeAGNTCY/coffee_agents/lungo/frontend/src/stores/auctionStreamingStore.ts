/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import { fetchNdjsonStream, ndjsonStreamUserMessage } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import type { HttpRequestTarget } from "@/urls"
import { isLocalDev } from "@/utils/const.ts"
import { logger } from "@/utils/logger"
import type { AuctionStreamingResponse } from "./auctionStreaming.types"
import {
  NDJSON_STREAMING_STATUS,
  type NdjsonStreamingStatus,
} from "./ndjsonStreamingStatus"

const isValidAuctionStreamingResponse = (
  data: unknown,
): data is AuctionStreamingResponse => {
  if (!data || typeof data !== "object") return false
  const obj = data as Record<string, unknown>
  const response = obj.response
  return typeof response === "string" && response.trim() !== ""
}

interface StreamingState {
  status: NdjsonStreamingStatus
  error: string | null
  events: AuctionStreamingResponse[]
  prompt: string | null
  abortController: AbortController | null
  sessionId: string | null
  connect: (
    prompt: string,
    workflowInstanceId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => Promise<void>
  disconnect: () => void
  reset: () => void
}

const initialState = {
  status: NDJSON_STREAMING_STATUS.IDLE,
  error: null,
  events: [],
  prompt: null,
  abortController: null,
  sessionId: null,
}

export const useAuctionStreamingStore = create<StreamingState>((set) => ({
  ...initialState,

  connect: async (
    prompt: string,
    workflowInstanceId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => {
    const abortController = new AbortController()

    set({
      status: NDJSON_STREAMING_STATUS.CONNECTING,
      error: null,
      prompt,
      events: [],
      abortController,
      sessionId: null,
    })

    if (!streamRequest?.url) {
      set({
        status: NDJSON_STREAMING_STATUS.ERROR,
        error: "Streaming request target is required",
        abortController: null,
      })
      return
    }

    try {
      await fetchNdjsonStream(streamRequest.url, {
        method: "POST",
        credentials: isLocalDev ? "omit" : "include",
        endpointLabel: streamRequest.endpointLabel,
        body: JSON.stringify({
          prompt,
          ...(workflowInstanceId
            ? { workflow_instance_id: workflowInstanceId }
            : {}),
        }),
        signal: abortController.signal,
        onStreamStart: () => {
          set({ status: NDJSON_STREAMING_STATUS.STREAMING })
        },
        onLine: (parsedData) => {
          if (isValidAuctionStreamingResponse(parsedData)) {
            set((state) => ({
              events: [...state.events, parsedData],
              sessionId: parsedData.session_id || state.sessionId,
            }))
          }
        },
        onParseError: (line, parseError) => {
          logger.warn("Failed to parse NDJSON line:", {
            line,
            parseError,
          })
        },
      })

      set({
        status: NDJSON_STREAMING_STATUS.COMPLETED,
        abortController: null,
      })
    } catch (error) {
      if (abortController.signal.aborted) return

      const httpError = reportRequestError(streamRequest.endpointLabel, error)
      set({
        status: NDJSON_STREAMING_STATUS.ERROR,
        error: ndjsonStreamUserMessage(httpError, "short"),
        abortController: null,
      })
    }
  },

  disconnect: () => {
    const { abortController } = useAuctionStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set({ status: NDJSON_STREAMING_STATUS.IDLE, abortController: null })
  },

  reset: () => {
    const { abortController } = useAuctionStreamingStore.getState()
    if (abortController) {
      abortController.abort()
    }
    set(initialState)
  },
}))

export const useStreamingStatus = () =>
  useAuctionStreamingStore((state) => state.status)

export const useStreamingError = () =>
  useAuctionStreamingStore((state) => state.error)

export const useStreamingEvents = () =>
  useAuctionStreamingStore((state) => state.events)

export const useStreamingPrompt = () =>
  useAuctionStreamingStore((state) => state.prompt)

export const useStreamingSessionId = () =>
  useAuctionStreamingStore((state) => state.sessionId)

export const useStreamingActions = () =>
  useAuctionStreamingStore((state) => ({
    connect: state.connect,
    disconnect: state.disconnect,
    reset: state.reset,
  }))
