/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { isHttpError, isRequestCancelledError } from "@/api/http"
import { CHAT_RETRY_CONFIG } from "@/config/requestRetryPolicy"

/**
 * Wait `ms`, rejecting with an AbortError as soon as `signal` aborts so a
 * backoff never outlives the request it belongs to.
 */
export const sleepMs = (ms: number, signal?: AbortSignal): Promise<void> =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Aborted", "AbortError"))
      return
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort)
      resolve()
    }, ms)
    const onAbort = () => {
      clearTimeout(timer)
      reject(new DOMException("Aborted", "AbortError"))
    }
    signal?.addEventListener("abort", onAbort, { once: true })
  })

/**
 * Transport-level failure: the response never arrived, so no status is known
 * (connection refused, DNS, TLS). Cancellations are excluded - both a client
 * timeout and our own teardown surface as aborts, and only the caller knows
 * which one it is looking at.
 */
export function isTransportFailureError(error: unknown): boolean {
  if (isRequestCancelledError(error)) return false
  return isHttpError(error) && error.status === undefined
}

/** True when `error` is an `HttpError` carrying one of `statuses`. */
export function hasRetryableStatus(
  error: unknown,
  statuses: readonly number[],
): boolean {
  return isHttpError(error) && statuses.includes(error.status ?? -1)
}

export const withRetry = async <T>(
  operation: () => Promise<T>,
  onRetry?: (attempt: number) => void,
  signal?: AbortSignal,
): Promise<T> => {
  let lastError: Error

  for (
    let attempt = 1;
    attempt <= CHAT_RETRY_CONFIG.maxRetries + 1;
    attempt++
  ) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error

      if (attempt > CHAT_RETRY_CONFIG.maxRetries) {
        throw lastError
      }

      // A cancellation and a client timeout reach here in the same shape, so
      // the caller's own signal is the only thing that tells them apart.
      if (signal?.aborted || !isRetryableError(error)) {
        throw lastError
      }

      if (onRetry) {
        onRetry(attempt)
      }

      const delay =
        CHAT_RETRY_CONFIG.baseDelay *
        Math.pow(CHAT_RETRY_CONFIG.backoffMultiplier, attempt - 1)
      await sleepMs(delay, signal)
    }
  }

  throw lastError!
}

const RETRYABLE_CODES = [
  "ECONNREFUSED",
  "ETIMEDOUT",
  "ENOTFOUND",
  "ECONNRESET",
] as const

/** Worth another attempt: 5xx, 429, transport codes, or no status at all. */
export function isRetryableError(error: unknown): boolean {
  if (typeof error !== "object" || error === null) return false

  const err = error as Record<string, unknown>

  if (
    typeof err.code === "string" &&
    (RETRYABLE_CODES as readonly string[]).includes(err.code)
  ) {
    return true
  }

  if (isHttpError(error)) {
    if (error.status === undefined) return true
    return error.status >= 500 || error.status === 429
  }

  return false
}
