/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import type { HttpRequestTarget } from "@/urls"
import { logger } from "@/utils/logger"
import type { AuctionStreamingResponse } from "./auctionStreaming.types"
import {
  buildPromptStreamBody,
  createAbortableNdjsonStreamingActions,
  NDJSON_STREAMING_CORE_INITIAL,
  type NdjsonStreamingCoreState,
} from "./createNdjsonStreamingStore"
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

interface StreamingState extends NdjsonStreamingCoreState {
  events: AuctionStreamingResponse[]
  connect: (
    prompt: string,
    workflowInstanceId?: string | null,
    streamRequest?: HttpRequestTarget,
  ) => Promise<void>
  disconnect: () => void
  reset: () => void
}

const initialState: Omit<StreamingState, "connect" | "disconnect" | "reset"> = {
  ...NDJSON_STREAMING_CORE_INITIAL,
  events: [],
}

export const useAuctionStreamingStore = create<StreamingState>((set, get) => {
  const actions = createAbortableNdjsonStreamingActions<
    StreamingState,
    {
      prompt: string
      workflowInstanceId?: string | null
      streamRequest?: HttpRequestTarget
    }
  >({
    get,
    set,
    initialState: initialState as StreamingState,
    buildConnectingPatch: (args, abortController) => ({
      status: NDJSON_STREAMING_STATUS.CONNECTING,
      error: null,
      prompt: args.prompt,
      events: [],
      abortController,
      sessionId: null,
    }),
    buildRequestBody: (args) =>
      buildPromptStreamBody(args.prompt, args.workflowInstanceId),
    onLine: (parsedData, { set: setState }) => {
      if (isValidAuctionStreamingResponse(parsedData)) {
        setState((state) => ({
          events: [...state.events, parsedData],
          sessionId: parsedData.session_id || state.sessionId,
        }))
      }
    },
    onParseError: (line, parseError) => {
      logger.warn("Failed to parse NDJSON line:", { line, parseError })
    },
  })

  return {
    ...initialState,
    connect: (
      prompt: string,
      workflowInstanceId?: string | null,
      streamRequest?: HttpRequestTarget,
    ) => actions.connect({ prompt, workflowInstanceId, streamRequest }),
    disconnect: actions.disconnect,
    reset: actions.reset,
  }
})

export const useStreamingStatus = (): NdjsonStreamingStatus =>
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
