/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { HttpError, REQUEST_CANCELLED_MESSAGE } from "@/api/http"
import {
  CHAT_RETRY_CONFIG,
  CHAT_RETRY_DELAYS_MS,
} from "@/config/requestRetryPolicy"
import { isRetryableError, withRetry, withRetryPolicy } from "./retryUtils"

const transportFailure = (): HttpError =>
  new HttpError("Network error. Please check your connection.")

const serverError = (): HttpError =>
  new HttpError("Service unavailable", { status: 503 })

const badRequest = (): HttpError =>
  new HttpError("Bad request", { status: 400 })

/** What `httpFetch` wraps an aborted fetch into: no status, cancelled message. */
const cancelledRequest = (): HttpError =>
  new HttpError(REQUEST_CANCELLED_MESSAGE)

const TOTAL_ATTEMPTS = CHAT_RETRY_CONFIG.maxRetries + 1

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

/** Attach the rejection handler now so a later rejection is never "unhandled". */
const settle = <T>(promise: Promise<T>) =>
  promise.then(
    (value) => ({ status: "resolved" as const, value }),
    (error: unknown) => ({ status: "rejected" as const, error }),
  )

describe("isRetryableError", () => {
  it("treats a cancelled request as retryable on its own", () => {
    // Pinned on purpose: cancellation and a client timeout have the same
    // shape, so this predicate cannot tell them apart. `withRetry` relies on
    // the caller's AbortSignal for that, and these tests guard that seam.
    expect(isRetryableError(cancelledRequest())).toBe(true)
  })

  it("does not retry a 4xx", () => {
    expect(isRetryableError(badRequest())).toBe(false)
  })
})

describe("withRetry", () => {
  it("returns the result without retrying when the first attempt succeeds", async () => {
    const operation = vi.fn().mockResolvedValue("ok")

    await expect(withRetry(operation)).resolves.toBe("ok")
    expect(operation).toHaveBeenCalledTimes(1)
  })

  it("retries a retryable failure with the chat backoff and reports 1-based attempts", async () => {
    const operation = vi
      .fn()
      .mockRejectedValueOnce(serverError())
      .mockRejectedValueOnce(transportFailure())
      .mockResolvedValue("ok")
    const onRetry = vi.fn()

    const result = settle(withRetry(operation, onRetry))
    await vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0])
    await vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[1])

    await expect(result).resolves.toEqual({ status: "resolved", value: "ok" })
    expect(operation).toHaveBeenCalledTimes(3)
    expect(onRetry.mock.calls).toEqual([[1], [2]])
  })

  it("waits for each backoff before the next attempt", async () => {
    const operation = vi
      .fn()
      .mockRejectedValueOnce(serverError())
      .mockResolvedValue("ok")

    const result = settle(withRetry(operation))
    await vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0] - 1)
    expect(operation).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1)
    expect(operation).toHaveBeenCalledTimes(2)
    await expect(result).resolves.toMatchObject({ status: "resolved" })
  })

  it("throws the last error once the budget is spent", async () => {
    const last = serverError()
    const operation = vi
      .fn()
      .mockRejectedValueOnce(transportFailure())
      .mockRejectedValueOnce(transportFailure())
      .mockRejectedValueOnce(transportFailure())
      .mockRejectedValue(last)

    const result = settle(withRetry(operation))
    await vi.runAllTimersAsync()

    await expect(result).resolves.toEqual({ status: "rejected", error: last })
    expect(operation).toHaveBeenCalledTimes(TOTAL_ATTEMPTS)
  })

  it("does not retry a non-retryable failure", async () => {
    const operation = vi.fn().mockRejectedValue(badRequest())
    const onRetry = vi.fn()

    await expect(withRetry(operation, onRetry)).rejects.toBeInstanceOf(
      HttpError,
    )
    expect(operation).toHaveBeenCalledTimes(1)
    expect(onRetry).not.toHaveBeenCalled()
  })

  describe("with a caller AbortSignal", () => {
    it("still retries a timeout-shaped failure while the signal is live", async () => {
      // A client timeout aborts httpFetch's private controller, not the
      // caller's signal, so it must remain retryable.
      const controller = new AbortController()
      const operation = vi
        .fn()
        .mockRejectedValueOnce(cancelledRequest())
        .mockResolvedValue("ok")

      const result = settle(withRetry(operation, undefined, controller.signal))
      await vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0])

      await expect(result).resolves.toEqual({
        status: "resolved",
        value: "ok",
      })
      expect(operation).toHaveBeenCalledTimes(2)
    })

    it("stops when the signal aborted while the attempt was in flight", async () => {
      const controller = new AbortController()
      const cancelled = cancelledRequest()
      const operation = vi.fn(async () => {
        controller.abort()
        throw cancelled
      })
      const onRetry = vi.fn()

      const result = settle(withRetry(operation, onRetry, controller.signal))
      await vi.runAllTimersAsync()

      await expect(result).resolves.toEqual({
        status: "rejected",
        error: cancelled,
      })
      expect(operation).toHaveBeenCalledTimes(1)
      expect(onRetry).not.toHaveBeenCalled()
    })

    it("does not start a second attempt when aborted during backoff", async () => {
      const controller = new AbortController()
      const operation = vi.fn().mockRejectedValue(serverError())

      const result = settle(withRetry(operation, undefined, controller.signal))
      await vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0] / 2)
      expect(operation).toHaveBeenCalledTimes(1)

      controller.abort()
      await vi.runAllTimersAsync()

      await expect(result).resolves.toMatchObject({
        status: "rejected",
        error: expect.objectContaining({ name: "AbortError" }),
      })
      expect(operation).toHaveBeenCalledTimes(1)
    })

    it("does not retry when the signal was already aborted", async () => {
      const controller = new AbortController()
      controller.abort()
      const operation = vi.fn().mockRejectedValue(serverError())

      const result = settle(withRetry(operation, undefined, controller.signal))
      await vi.runAllTimersAsync()

      await expect(result).resolves.toMatchObject({ status: "rejected" })
      expect(operation).toHaveBeenCalledTimes(1)
    })
  })
})

describe("withRetryPolicy", () => {
  const policy = (
    over: Partial<Parameters<typeof withRetryPolicy>[1]> = {},
  ) => ({
    maxRetries: 2,
    delaysMs: [10, 20] as const,
    isRetryable: () => true,
    ...over,
  })

  it("repeats the last delay when retries outnumber delays", async () => {
    const operation = vi.fn().mockRejectedValue(serverError())

    const result = settle(
      withRetryPolicy(operation, policy({ maxRetries: 3, delaysMs: [10] })),
    )
    await vi.advanceTimersByTimeAsync(10)
    expect(operation).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(10)
    expect(operation).toHaveBeenCalledTimes(3)
    await vi.advanceTimersByTimeAsync(10)
    expect(operation).toHaveBeenCalledTimes(4)

    await expect(result).resolves.toMatchObject({ status: "rejected" })
  })

  it("consults the caller's retryable rule for every failure", async () => {
    const isRetryable = vi.fn(() => false)
    const operation = vi.fn().mockRejectedValue(serverError())

    await expect(
      withRetryPolicy(operation, policy({ isRetryable })),
    ).rejects.toBeInstanceOf(HttpError)
    expect(isRetryable).toHaveBeenCalledTimes(1)
    expect(operation).toHaveBeenCalledTimes(1)
  })

  it("makes a single attempt when maxRetries is zero", async () => {
    const operation = vi.fn().mockRejectedValue(serverError())

    await expect(
      withRetryPolicy(operation, policy({ maxRetries: 0 })),
    ).rejects.toBeInstanceOf(HttpError)
    expect(operation).toHaveBeenCalledTimes(1)
  })
})
