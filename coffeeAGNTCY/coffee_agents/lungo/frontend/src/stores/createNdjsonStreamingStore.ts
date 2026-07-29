/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared connect / abort / fetchNdjsonStream lifecycle for agent-prompt NDJSON stores.
 **/

import {
  fetchNdjsonStream,
  ndjsonStreamUserMessage,
  type NdjsonSplitMode,
} from "@/api/http"
import { reportRequestError } from "@/errors/request"
import type { HttpRequestTarget } from "@/urls"
import { isLocalDev } from "@/utils/const.ts"
import { logger } from "@/utils/logger"
import {
  NDJSON_STREAMING_STATUS,
  type NdjsonStreamingStatus,
} from "./ndjsonStreamingStatus"

export interface NdjsonStreamingCoreState {
  status: NdjsonStreamingStatus
  error: string | null
  prompt: string | null
  abortController: AbortController | null
  sessionId: string | null
}

export const NDJSON_STREAMING_CORE_INITIAL: NdjsonStreamingCoreState = {
  status: NDJSON_STREAMING_STATUS.IDLE,
  error: null,
  prompt: null,
  abortController: null,
  sessionId: null,
}

const MISSING_STREAM_TARGET = "Streaming request target is required"

export function logNdjsonLineParseWarning(line: string, parseError: unknown) {
  logger.warn("Failed to parse NDJSON line:", { line, parseError })
}

export async function runNdjsonStreamRequest(options: {
  streamRequest: HttpRequestTarget
  body: Record<string, unknown>
  signal?: AbortSignal
  splitMode?: NdjsonSplitMode
  onStreamStart: () => void
  onLine: (parsed: unknown) => "stop" | void
  onParseError?: (line: string, error: unknown) => void
}): Promise<void> {
  const {
    streamRequest,
    body,
    signal,
    splitMode,
    onStreamStart,
    onLine,
    onParseError,
  } = options

  await fetchNdjsonStream(streamRequest.url, {
    method: "POST",
    credentials: isLocalDev ? "omit" : "include",
    endpointLabel: streamRequest.endpointLabel,
    body: JSON.stringify(body),
    signal,
    splitMode,
    onStreamStart,
    onLine,
    onParseError,
  })
}

export function ndjsonStreamErrorMessage(
  endpointLabel: string,
  error: unknown,
  aborted: boolean,
): string | null {
  if (aborted) return null
  const httpError = reportRequestError(endpointLabel, error)
  return ndjsonStreamUserMessage(httpError, "short")
}

type StoreSetter<TState> = (
  partial: Partial<TState> | ((state: TState) => Partial<TState>),
  replace?: false,
) => void

type StoreGetter<TState> = () => TState

export type NdjsonStreamingConnectArgs = {
  prompt: string
  workflowInstanceId?: string | null
  streamRequest?: HttpRequestTarget
}

export function buildPromptStreamBody(
  prompt: string,
  workflowInstanceId?: string | null,
  extra?: Record<string, unknown>,
): Record<string, unknown> {
  return {
    prompt,
    ...(workflowInstanceId ? { workflow_instance_id: workflowInstanceId } : {}),
    ...extra,
  }
}

export function createAbortableNdjsonStreamingActions<
  TState extends NdjsonStreamingCoreState,
  TConnectArgs extends NdjsonStreamingConnectArgs,
>(config: {
  get: StoreGetter<TState>
  set: StoreSetter<TState>
  initialState: TState
  buildConnectingPatch: (
    args: TConnectArgs,
    abortController: AbortController,
  ) => Partial<TState>
  buildRequestBody: (args: TConnectArgs) => Record<string, unknown>
  onLine: (
    parsed: unknown,
    ctx: { get: StoreGetter<TState>; set: StoreSetter<TState> },
  ) => "stop" | void
  onParseError?: (line: string, error: unknown) => void
  guardCompletedOnError?: boolean
  splitMode?: NdjsonSplitMode
}) {
  const connect = async (args: TConnectArgs) => {
    const abortController = new AbortController()

    config.set({
      ...config.buildConnectingPatch(args, abortController),
    } as Partial<TState>)

    if (!args.streamRequest?.url) {
      config.set({
        status: NDJSON_STREAMING_STATUS.ERROR,
        error: MISSING_STREAM_TARGET,
        abortController: null,
      } as Partial<TState>)
      return
    }

    const streamRequest = args.streamRequest

    try {
      await runNdjsonStreamRequest({
        streamRequest,
        body: config.buildRequestBody(args),
        signal: abortController.signal,
        splitMode: config.splitMode,
        onStreamStart: () => {
          config.set({
            status: NDJSON_STREAMING_STATUS.STREAMING,
          } as Partial<TState>)
        },
        onLine: (parsed) =>
          config.onLine(parsed, { get: config.get, set: config.set }),
        onParseError: config.onParseError ?? logNdjsonLineParseWarning,
      })

      if (config.guardCompletedOnError) {
        if (config.get().status !== NDJSON_STREAMING_STATUS.ERROR) {
          config.set({
            status: NDJSON_STREAMING_STATUS.COMPLETED,
            abortController: null,
          } as Partial<TState>)
        }
      } else {
        config.set({
          status: NDJSON_STREAMING_STATUS.COMPLETED,
          abortController: null,
        } as Partial<TState>)
      }
    } catch (error) {
      const message = ndjsonStreamErrorMessage(
        streamRequest.endpointLabel,
        error,
        abortController.signal.aborted,
      )
      if (message === null) return

      config.set({
        status: NDJSON_STREAMING_STATUS.ERROR,
        error: message,
        abortController: null,
      } as Partial<TState>)
    }
  }

  const disconnect = () => {
    const { abortController } = config.get()
    if (abortController) {
      abortController.abort()
    }
    config.set({
      status: NDJSON_STREAMING_STATUS.IDLE,
      abortController: null,
    } as Partial<TState>)
  }

  const reset = () => {
    const { abortController } = config.get()
    if (abortController) {
      abortController.abort()
    }
    config.set(config.initialState)
  }

  return { connect, disconnect, reset }
}

/** NDJSON session without abort/disconnect (group messaging stream). */
export async function runNdjsonStreamingSession(options: {
  streamRequest?: HttpRequestTarget
  onMissingTarget: () => void
  buildBody: () => Record<string, unknown>
  splitMode?: NdjsonSplitMode
  onStreamStart: () => void
  onLine: (parsed: unknown) => "stop" | void
  onParseError: (line: string, error: unknown) => void
  isErrorStatus: () => boolean
  onCompleted: () => void
  onFailed: (message: string) => void
}): Promise<void> {
  if (!options.streamRequest?.url) {
    options.onMissingTarget()
    return
  }

  const streamRequest = options.streamRequest

  try {
    await runNdjsonStreamRequest({
      streamRequest,
      body: options.buildBody(),
      splitMode: options.splitMode,
      onStreamStart: options.onStreamStart,
      onLine: options.onLine,
      onParseError: options.onParseError,
    })

    if (!options.isErrorStatus()) {
      options.onCompleted()
    }
  } catch (error) {
    const message = ndjsonStreamErrorMessage(
      streamRequest.endpointLabel,
      error,
      false,
    )
    if (message !== null) {
      options.onFailed(message)
    }
  }
}
