/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { act, renderHook } from "@testing-library/react"
import { HttpError, REQUEST_CANCELLED_MESSAGE } from "@/api/http"
import { CHAT_RETRY_DELAYS_MS } from "@/config/requestRetryPolicy"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"

const fetchJson = vi.fn()

vi.mock("@/api/http", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/http")>()
  return { ...actual, fetchJson: (...args: unknown[]) => fetchJson(...args) }
})

vi.mock("@/errors/request", () => ({ reportRequestError: vi.fn() }))

const { useAgentAPI } = await import("./useAgentAPI")

/** `supports_sse` is what turns chat retries on. */
const RETRYING_WORKFLOW: WorkflowSummary = {
  name: "Workflow",
  pattern: "publish_subscribe",
  pattern_category: "Orchestration & Control Flow",
  use_case: "use",
  scenario: "scenario",
  supports_sse: true,
  supports_streaming: false,
  chat_api_target: "exchange",
}

const transportFailure = (): HttpError =>
  new HttpError("Network error. Please check your connection.")

/** An in-flight request that fails the way `httpFetch` does when aborted. */
const hangUntilAborted = (_url: string, init: { signal: AbortSignal }) =>
  new Promise<never>((_resolve, reject) => {
    init.signal.addEventListener("abort", () =>
      reject(new HttpError(REQUEST_CANCELLED_MESSAGE)),
    )
  })

const settle = <T>(promise: Promise<T>) =>
  promise.then(
    (value) => ({ status: "resolved" as const, value }),
    (error: unknown) => ({ status: "rejected" as const, error }),
  )

beforeEach(() => {
  vi.useFakeTimers()
  fetchJson.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe("useAgentAPI retries", () => {
  it("retries a transport failure while the request is live (control)", async () => {
    fetchJson
      .mockRejectedValueOnce(transportFailure())
      .mockResolvedValue({ response: "hello" })
    const { result } = renderHook(() => useAgentAPI())

    const outcome = settle(result.current.sendMessage("hi", RETRYING_WORKFLOW))
    await act(() => vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0]))

    await expect(outcome).resolves.toEqual({
      status: "resolved",
      value: { response: "hello" },
    })
    expect(fetchJson).toHaveBeenCalledTimes(2)
  })

  describe("sendMessage", () => {
    it("does not retry a request that was cancelled while in flight", async () => {
      fetchJson.mockImplementation(hangUntilAborted)
      const { result } = renderHook(() => useAgentAPI())

      const outcome = settle(
        result.current.sendMessage("hi", RETRYING_WORKFLOW),
      )
      await act(() => vi.advanceTimersByTimeAsync(0))
      expect(fetchJson).toHaveBeenCalledTimes(1)

      act(() => result.current.cancel())
      await act(() => vi.runAllTimersAsync())

      await expect(outcome).resolves.toMatchObject({ status: "rejected" })
      expect(fetchJson).toHaveBeenCalledTimes(1)
    })

    it("does not fire another request when cancelled while backing off", async () => {
      fetchJson.mockRejectedValue(transportFailure())
      const { result } = renderHook(() => useAgentAPI())

      const outcome = settle(
        result.current.sendMessage("hi", RETRYING_WORKFLOW),
      )
      await act(() => vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0] / 2))
      expect(fetchJson).toHaveBeenCalledTimes(1)

      act(() => result.current.cancel())
      await act(() => vi.runAllTimersAsync())

      await expect(outcome).resolves.toMatchObject({ status: "rejected" })
      expect(fetchJson).toHaveBeenCalledTimes(1)
    })

    it("does not fire another request once the component unmounts", async () => {
      fetchJson.mockRejectedValue(transportFailure())
      const { result, unmount } = renderHook(() => useAgentAPI())

      const outcome = settle(
        result.current.sendMessage("hi", RETRYING_WORKFLOW),
      )
      await act(() => vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0] / 2))

      unmount()
      await vi.runAllTimersAsync()

      await expect(outcome).resolves.toMatchObject({ status: "rejected" })
      expect(fetchJson).toHaveBeenCalledTimes(1)
    })
  })

  describe("sendMessageWithCallback", () => {
    const setMessages = vi.fn()

    it("does not retry a request that was cancelled while in flight", async () => {
      fetchJson.mockImplementation(hangUntilAborted)
      const onRetryAttempt = vi.fn()
      const { result } = renderHook(() => useAgentAPI())

      const outcome = result.current.sendMessageWithCallback(
        "hi",
        setMessages,
        { onRetryAttempt },
        RETRYING_WORKFLOW,
      )
      await act(() => vi.advanceTimersByTimeAsync(0))

      act(() => result.current.cancel())
      await act(() => vi.runAllTimersAsync())
      await outcome

      expect(fetchJson).toHaveBeenCalledTimes(1)
      expect(onRetryAttempt).not.toHaveBeenCalled()
    })

    it("stops the retry countdown when cancelled while backing off", async () => {
      fetchJson.mockRejectedValue(transportFailure())
      const onRetryAttempt = vi.fn()
      const { result } = renderHook(() => useAgentAPI())

      const outcome = result.current.sendMessageWithCallback(
        "hi",
        setMessages,
        { onRetryAttempt },
        RETRYING_WORKFLOW,
      )
      await act(() => vi.advanceTimersByTimeAsync(CHAT_RETRY_DELAYS_MS[0] / 2))
      expect(onRetryAttempt).toHaveBeenCalledTimes(1)

      act(() => result.current.cancel())
      await act(() => vi.runAllTimersAsync())
      await outcome

      expect(fetchJson).toHaveBeenCalledTimes(1)
      expect(onRetryAttempt).toHaveBeenCalledTimes(1)
    })
  })
})
