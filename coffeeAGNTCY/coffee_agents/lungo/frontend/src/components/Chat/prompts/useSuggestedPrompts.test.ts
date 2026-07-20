/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { fetchJson } from "@/api/http"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { useSuggestedPrompts } from "./useSuggestedPrompts"
import { MAX_SUGGESTED_PROMPTS_RETRIES } from "./suggestedPromptsUtils"

vi.mock("@/api/http", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/http")>()
  return {
    ...actual,
    fetchJson: vi.fn(),
  }
})

vi.mock("./suggestedPromptsUtils", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("./suggestedPromptsUtils")>()
  return {
    ...actual,
    getRetryDelayMs: () => 0,
  }
})

vi.mock("@/errors/request", () => ({
  reportRequestError: vi.fn(),
}))

import { reportRequestError } from "@/errors/request"

const coffeePromptsRequest = {
  url: "https://exchange.test/suggested-prompts",
  endpointLabel: LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts.endpointLabel,
}

const logisticsPromptsRequest = {
  url: "https://logistics.test/suggested-prompts",
  endpointLabel: LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts.endpointLabel,
}

const discoveryPromptsRequest = {
  url: "https://discovery.test/suggested-prompts",
  endpointLabel: LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts.endpointLabel,
}

describe("useSuggestedPrompts", () => {
  beforeEach(() => {
    vi.mocked(reportRequestError).mockClear()
    vi.mocked(fetchJson).mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("loads prompt categories on success", async () => {
    vi.mocked(fetchJson).mockResolvedValue({
      General: [{ prompt: "Hello", description: "Say hi" }],
    })

    const { result } = renderHook(() =>
      useSuggestedPrompts(coffeePromptsRequest),
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.isUnavailable).toBe(false)
    expect(result.current.categories).toEqual([
      {
        name: "General",
        prompts: [{ prompt: "Hello", description: "Say hi" }],
      },
    ])
    expect(fetchJson).toHaveBeenCalledWith(
      coffeePromptsRequest.url,
      expect.objectContaining({
        endpointLabel: coffeePromptsRequest.endpointLabel,
      }),
    )
    expect(reportRequestError).not.toHaveBeenCalled()
  })

  it("reports and marks unavailable after retries are exhausted", async () => {
    vi.mocked(fetchJson).mockRejectedValue(new Error("network down"))

    const { result } = renderHook(() =>
      useSuggestedPrompts(logisticsPromptsRequest),
    )

    await waitFor(() => {
      expect(result.current.isUnavailable).toBe(true)
    })

    expect(result.current.categories).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(fetchJson).toHaveBeenCalledTimes(MAX_SUGGESTED_PROMPTS_RETRIES + 1)
    expect(reportRequestError).toHaveBeenCalledTimes(1)
    expect(reportRequestError).toHaveBeenCalledWith(
      logisticsPromptsRequest.endpointLabel,
      expect.any(Error),
    )
  })

  it("retries empty prompt payloads before marking unavailable", async () => {
    vi.mocked(fetchJson)
      .mockResolvedValueOnce({ General: [] })
      .mockResolvedValueOnce({ General: [] })
      .mockResolvedValue({
        General: [{ prompt: "Ship order", description: "Track delivery" }],
      })

    const { result } = renderHook(() =>
      useSuggestedPrompts(discoveryPromptsRequest),
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.isUnavailable).toBe(false)
    expect(result.current.categories[0]?.prompts).toHaveLength(1)
    expect(fetchJson).toHaveBeenCalledTimes(3)
    expect(reportRequestError).not.toHaveBeenCalled()
  })
})
