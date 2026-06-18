/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useEffect, useRef } from "react"
import { getAgenticWorkflowsApiUrl } from "@/urls"
import { agenticWorkflowsAuthHeaders } from "@/api/agenticWorkflowsClient"

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

const parseFrame = (raw: string): PatternChatFrame | null => {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  if (isResponseFrame(parsed)) return parsed
  if (isDoneFrame(parsed)) return parsed
  if (isErrorFrame(parsed)) return parsed
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

      const url = `${getAgenticWorkflowsApiUrl()}/patterns/${encodeURIComponent(patternName)}/chat`

      let response: Response
      try {
        response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...agenticWorkflowsAuthHeaders(),
          },
          body: JSON.stringify({ session_id: sessionId, message }),
          signal: controller.signal,
        })
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return
        onError(
          new PatternChatTransportError(
            err instanceof Error ? err.message : String(err),
          ),
        )
        return
      }

      if (response.status === 404) {
        onError(new PatternChatNotFoundError(patternName))
        return
      }
      if (!response.ok) {
        onError(
          new PatternChatTransportError(
            `HTTP ${response.status} ${response.statusText}`,
          ),
        )
        return
      }
      if (response.body === null) {
        onError(new PatternChatTransportError("Response body was empty"))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let sawDone = false

      try {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          let nl = buffer.indexOf("\n")
          while (nl !== -1) {
            const line = buffer.slice(0, nl).trim()
            buffer = buffer.slice(nl + 1)
            if (line.length > 0) {
              const frame = parseFrame(line)
              if (frame === null) {
                onError(
                  new PatternChatTransportError(
                    `Malformed NDJSON frame: ${line.slice(0, 80)}`,
                  ),
                )
                return
              }
              if (isErrorFrame(frame)) {
                onError(new Error(frame.error))
                return
              }
              if (isDoneFrame(frame)) {
                sawDone = true
                onDone()
                return
              }
              onChunk(frame.response)
            }
            nl = buffer.indexOf("\n")
          }
        }
        const tail = buffer.trim()
        if (tail.length > 0) {
          const frame = parseFrame(tail)
          if (frame !== null) {
            if (isErrorFrame(frame)) {
              onError(new Error(frame.error))
              return
            }
            if (isDoneFrame(frame)) {
              sawDone = true
              onDone()
              return
            }
            onChunk(frame.response)
          }
        }
        if (!sawDone) {
          onError(
            new PatternChatTransportError("Stream ended without a done frame"),
          )
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return
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
