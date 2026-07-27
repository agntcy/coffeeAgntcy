/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { parseHttpError, parseHttpErrorFromResponse } from "./parseHttpError.ts"
import { HttpError } from "./types.ts"

type FetchInit = NonNullable<Parameters<typeof fetch>[1]>

export type HttpFetchOptions = FetchInit & {
  /** Request timeout in milliseconds. Defaults to 60_000. */
  timeoutMs?: number
  /** Logical endpoint label used in HttpError reporting. */
  endpointLabel?: string
}

export async function httpFetch(
  url: string,
  options: HttpFetchOptions = {},
): Promise<Response> {
  const { timeoutMs = 60_000, endpointLabel = url, ...init } = options
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  if (init.signal) {
    if (init.signal.aborted) {
      controller.abort()
    } else {
      init.signal.addEventListener("abort", () => controller.abort(), {
        once: true,
      })
    }
  }

  try {
    const response = await fetch(url, {
      ...init,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw await parseHttpErrorFromResponse(response, { endpointLabel })
    }

    return response
  } catch (error) {
    if (error instanceof HttpError) {
      throw error
    }

    throw parseHttpError(error, { endpointLabel })
  } finally {
    clearTimeout(timeoutId)
  }
}
