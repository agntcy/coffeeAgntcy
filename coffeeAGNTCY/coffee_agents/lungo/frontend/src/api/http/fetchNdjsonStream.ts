/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { httpFetch, type HttpFetchOptions } from "./httpClient.ts"
import {
  consumeJsonObjectsFromBuffer,
  consumeNdjsonLines,
  type NdjsonLineHandler,
  type NdjsonParseErrorHandler,
} from "./ndjsonParsing.ts"
import { HttpError } from "./types.ts"

type FetchInit = NonNullable<Parameters<typeof fetch>[1]>

export type NdjsonSplitMode = "lines" | "json-objects"

export type FetchNdjsonStreamOptions = Omit<
  FetchInit,
  "headers" | "signal" | "body"
> &
  Pick<HttpFetchOptions, "endpointLabel" | "timeoutMs"> & {
    body?: FetchInit extends { body?: infer B } ? B : never
    headers?: Record<string, string>
    signal?: AbortSignal
    /** How complete JSON records are delimited in the response body. */
    splitMode?: NdjsonSplitMode
    onLine: NdjsonLineHandler
    onParseError?: NdjsonParseErrorHandler
    /** Invoked after the HTTP response is validated and body reading begins. */
    onStreamStart?: () => void
  }

/**
 * POST (or other method) to a streaming endpoint, validate the response with
 * {@link httpFetch}, then read NDJSON frames from the body.
 */
export async function fetchNdjsonStream(
  url: string,
  options: FetchNdjsonStreamOptions,
): Promise<void> {
  const {
    endpointLabel = url,
    splitMode = "lines",
    onLine,
    onParseError,
    onStreamStart,
    headers,
    signal,
    timeoutMs,
    ...init
  } = options

  const response = await httpFetch(url, {
    ...init,
    endpointLabel,
    timeoutMs,
    signal,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  })

  if (!response.body) {
    throw new HttpError(
      "Response body is not readable - streaming not supported",
      {
        status: response.status,
        endpointLabel,
      },
    )
  }

  onStreamStart?.()

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let stopped = false

  try {
    while (!stopped) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      if (splitMode === "lines") {
        buffer = consumeNdjsonLines(
          buffer,
          (parsed, raw) => {
            if (onLine(parsed, raw) === "stop") {
              stopped = true
              return "stop"
            }
          },
          onParseError,
        )
      } else {
        buffer = consumeJsonObjectsFromBuffer(
          buffer,
          (parsed, raw) => {
            if (onLine(parsed, raw) === "stop") {
              stopped = true
              return "stop"
            }
          },
          onParseError,
        )
      }
    }

    if (stopped) return

    if (splitMode === "lines") {
      const trimmed = buffer.trim()
      if (trimmed) {
        try {
          onLine(JSON.parse(trimmed) as unknown, trimmed)
        } catch (error) {
          onParseError?.(trimmed, error)
        }
      }
    } else if (buffer.trim()) {
      consumeJsonObjectsFromBuffer(buffer, onLine, onParseError)
    }
  } finally {
    reader.releaseLock()
  }
}
