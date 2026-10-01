/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { isHttpError, isRequestCancelledError } from "@/api/http"
import {
  CHAT_RETRY_CONFIG,
  CHAT_RETRY_DELAYS_MS,
} from "@/config/requestRetryPolicy"

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

export interface RetryPolicy {
  /** Retries after the first try, so the operation runs `maxRetries + 1` times. */
  maxRetries: number
  /** Backoff per retry. The last entry repeats if retries outnumber delays. */
  delaysMs: readonly number[]
  isRetryable: (error: unknown) => boolean
  /** Called before each backoff with the 1-based retry number. */
  onRetry?: (attempt: number) => void
  /**
   * Aborting ends the loop. A cancellation and a client timeout surface in the
   * same shape, so the caller's signal is the only thing that tells them apart.
   */
  signal?: AbortSignal
}

/**
 * The one retry loop. Budgets, backoff, and the retryable-error rule are all
 * caller-supplied, because they differ per feature - see
 * `@/config/requestRetryPolicy`.
 */
export async function withRetryPolicy<T>(
  operation: () => Promise<T>,
  { maxRetries, delaysMs, isRetryable, onRetry, signal }: RetryPolicy,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    try {
      return await operation()
    } catch (error) {
      const isFinalAttempt = attempt === maxRetries
      if (isFinalAttempt || signal?.aborted || !isRetryable(error)) {
        throw error
      }
      onRetry?.(attempt + 1)
      await sleepMs(delaysMs[attempt] ?? delaysMs[delaysMs.length - 1], signal)
    }
  }

  // Unreachable: the loop runs at least once and every path returns or throws.
  throw new Error("withRetryPolicy exhausted without a result")
}

/** Chat prompts: exponential backoff on the shared retryable-error rule. */
export const withRetry = <T>(
  operation: () => Promise<T>,
  onRetry?: (attempt: number) => void,
  signal?: AbortSignal,
): Promise<T> =>
  withRetryPolicy(operation, {
    maxRetries: CHAT_RETRY_CONFIG.maxRetries,
    delaysMs: CHAT_RETRY_DELAYS_MS,
    isRetryable: isRetryableError,
    onRetry,
    signal,
  })

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
