/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useRef } from "react"
import { fetchNdjsonStream, isHttpError } from "@/api/http"
import { agenticWorkflowsAuthHeaders } from "@/api/agenticWorkflowsClient"
import { reportRequestError } from "@/errors/request"
import { buildAgenticWorkflowsPatternChatRequest } from "@/urls"

export class PatternChatNotFoundError extends Error {
  constructor(patternName: string) {
    super(`Pattern chat not available for: ${patternName}`)
    this.name = "PatternChatNotFoundError"
  }
}

export class PatternChatTransportError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "PatternChatTransportError"
  }
}

export interface PatternChatRequest {
  patternName: string
  sessionId: string
  message: string
}

export interface PatternChatCallbacks {
  onChunk: (text: string) => void
  onDone: () => void
  onError: (err: Error) => void
}

interface PatternChatFrameResponse {
  response: string
}

interface PatternChatFrameDone {
  done: true
}

interface PatternChatFrameError {
  error: string
}

type PatternChatFrame =
  | PatternChatFrameResponse
  | PatternChatFrameDone
  | PatternChatFrameError

const isResponseFrame = (v: unknown): v is PatternChatFrameResponse =>
  typeof v === "object" &&
  v !== null &&
  "response" in v &&
  typeof (v as { response: unknown }).response === "string"

const isDoneFrame = (v: unknown): v is PatternChatFrameDone =>
  typeof v === "object" &&
  v !== null &&
  "done" in v &&
  (v as { done: unknown }).done === true

const isErrorFrame = (v: unknown): v is PatternChatFrameError =>
  typeof v === "object" &&
  v !== null &&
  "error" in v &&
  typeof (v as { error: unknown }).error === "string"

const parseFrame = (raw: unknown): PatternChatFrame | null => {
  if (isResponseFrame(raw)) return raw
  if (isDoneFrame(raw)) return raw
  if (isErrorFrame(raw)) return raw
  return null
}

export interface UsePatternChatAPIReturn {
  sendPatternMessage: (
    req: PatternChatRequest,
    callbacks: PatternChatCallbacks,
  ) => Promise<void>
  cancel: () => void
}

export const usePatternChatAPI = (): UsePatternChatAPIReturn => {
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  const sendPatternMessage = useCallback(
    async (
      { patternName, sessionId, message }: PatternChatRequest,
      { onChunk, onDone, onError }: PatternChatCallbacks,
    ): Promise<void> => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      const chatRequest = buildAgenticWorkflowsPatternChatRequest(patternName)
      let sawDone = false
      let streamError: Error | null = null

      try {
        await fetchNdjsonStream(chatRequest.url, {
          method: "POST",
          headers: {
            ...agenticWorkflowsAuthHeaders(),
          },
          body: JSON.stringify({ session_id: sessionId, message }),
          signal: controller.signal,
          endpointLabel: chatRequest.endpointLabel,
          onLine: (rawFrame, line) => {
            if (streamError) return "stop"

            const frame = parseFrame(rawFrame)
            if (frame === null) {
              streamError = new PatternChatTransportError(
                `Malformed NDJSON frame: ${line.slice(0, 80)}`,
              )
              return "stop"
            }
            if (isErrorFrame(frame)) {
              streamError = new Error(frame.error)
              return "stop"
            }
            if (isDoneFrame(frame)) {
              sawDone = true
              onDone()
              return "stop"
            }
            onChunk(frame.response)
          },
        })

        if (streamError) {
          reportRequestError(chatRequest.endpointLabel, streamError)
          onError(streamError)
          return
        }

        if (!sawDone) {
          const err = new PatternChatTransportError(
            "Stream ended without a done frame",
          )
          reportRequestError(chatRequest.endpointLabel, err)
          onError(err)
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return
        if (isHttpError(err) && err.status === 404) {
          reportRequestError(chatRequest.endpointLabel, err)
          onError(new PatternChatNotFoundError(patternName))
          return
        }
        if (isHttpError(err)) {
          reportRequestError(chatRequest.endpointLabel, err)
          onError(
            new PatternChatTransportError(
              `HTTP ${err.status ?? "?"} - ${err.message}`,
            ),
          )
          return
        }
        reportRequestError(chatRequest.endpointLabel, err)
        onError(
          new PatternChatTransportError(
            err instanceof Error ? err.message : String(err),
          ),
        )
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null
        }
      }
    },
    [],
  )

  return { sendPatternMessage, cancel }
}
