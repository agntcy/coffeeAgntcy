/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { parseHttpError, parseHttpErrorFromResponse } from "./parseHttpError.ts"
import { HttpError } from "./types.ts"
import { parseSseFrameLines, splitSseFrames } from "./sseParsing.ts"

type FetchInit = NonNullable<Parameters<typeof fetch>[1]>

export type FetchSseOptions<T> = Omit<FetchInit, "headers" | "signal"> & {
  headers?: Record<string, string>
  signal?: AbortSignal
  /** Logical endpoint label used in HttpError reporting. */
  endpointLabel?: string
  onEvent: (event: T) => void
  onError?: (error: unknown) => void
}

export type FetchSseClose = () => void

/**
 * Open an SSE stream, parse `data:` JSON lines, and invoke `onEvent` for each frame.
 * Returns a close function that aborts the underlying fetch.
 */
export function fetchSse<T>(
  url: string,
  options: FetchSseOptions<T>,
): FetchSseClose {
  const {
    endpointLabel = url,
    onEvent,
    onError,
    headers,
    signal,
    ...init
  } = options

  let aborted = false
  let buffer = ""
  const controller = new AbortController()

  if (signal) {
    if (signal.aborted) {
      controller.abort()
    } else {
      signal.addEventListener("abort", () => controller.abort(), { once: true })
    }
  }

  const run = async (): Promise<void> => {
    try {
      const response = await fetch(url, {
        ...init,
        headers: {
          Accept: "text/event-stream",
          ...headers,
        },
        cache: "no-store",
        signal: controller.signal,
      })

      if (!response.ok) {
        onError?.(await parseHttpErrorFromResponse(response, { endpointLabel }))
        return
      }

      if (!response.body) {
        onError?.(
          new HttpError("SSE response has no body.", {
            status: response.status,
            endpointLabel,
          }),
        )
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (!aborted) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const { frames, remainder } = splitSseFrames(buffer)
        buffer = remainder
        for (const frame of frames) {
          const events = parseSseFrameLines<T>(frame)
          for (const event of events) onEvent(event)
        }
      }
    } catch (error) {
      if (controller.signal.aborted || aborted) return
      if (error instanceof HttpError) {
        onError?.(error)
        return
      }
      onError?.(parseHttpError(error, { endpointLabel }))
    }
  }

  void run()

  return () => {
    aborted = true
    controller.abort()
  }
}
