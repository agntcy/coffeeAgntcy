/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000,
  backoffMultiplier: 2,
}

export const withRetry = async <T>(
  operation: () => Promise<T>,
  onRetry?: (attempt: number) => void,
): Promise<T> => {
  let lastError: Error

  for (let attempt = 1; attempt <= RETRY_CONFIG.maxRetries + 1; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error

      if (attempt > RETRY_CONFIG.maxRetries) {
        throw lastError
      }

      if (!isRetryableError(error)) {
        throw lastError
      }

      if (onRetry) {
        onRetry(attempt)
      }

      const delay =
        RETRY_CONFIG.baseDelay *
        Math.pow(RETRY_CONFIG.backoffMultiplier, attempt - 1)
      await new Promise((resolve) => setTimeout(resolve, delay))
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

function isRetryableError(error: unknown): boolean {
  if (typeof error !== "object" || error === null) return false

  const err = error as Record<string, unknown>

  if (
    typeof err.code === "string" &&
    (RETRYABLE_CODES as readonly string[]).includes(err.code)
  ) {
    return true
  }

  if (err.isAxiosError) {
    if (!err.response) return true
    const response = err.response as { status?: number }
    const status = response.status
    return typeof status === "number" && (status >= 500 || status === 429)
  }

  return false
}
