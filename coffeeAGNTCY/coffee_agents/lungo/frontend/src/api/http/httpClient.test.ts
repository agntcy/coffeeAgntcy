/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { httpFetch, HttpError, isHttpError } from "@/api/http"

type FetchInit = NonNullable<Parameters<typeof fetch>[1]>

function mockFetchThatRejectsOnAbort() {
  return vi.fn((_url: string, init?: FetchInit) => {
    return new Promise<Response>((_resolve, reject) => {
      const signal = init?.signal
      if (signal?.aborted) {
        reject(new DOMException("The operation was aborted.", "AbortError"))
        return
      }

      signal?.addEventListener(
        "abort",
        () => {
          reject(new DOMException("The operation was aborted.", "AbortError"))
        },
        { once: true },
      )
    })
  })
}

describe("httpFetch", () => {
  beforeEach(() => {
    vi.useRealTimers()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it("returns the Response for successful requests", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("ok", { status: 200 })),
    )

    const response = await httpFetch("https://api.test/resource")
    expect(response.ok).toBe(true)
    expect(await response.text()).toBe("ok")
  })

  it("throws HttpError for non-OK responses with parsed FastAPI detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Not allowed" }), {
          status: 403,
          headers: { "content-type": "application/json" },
        }),
      ),
    )

    await expect(
      httpFetch("https://api.test/resource", { endpointLabel: "/resource" }),
    ).rejects.toSatisfy((error: unknown) => {
      expect(isHttpError(error)).toBe(true)
      expect((error as HttpError).status).toBe(403)
      expect((error as HttpError).message).toBe("Not allowed")
      expect((error as HttpError).endpointLabel).toBe("/resource")
      return true
    })
  })

  it("maps network failures to HttpError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    )

    await expect(
      httpFetch("https://api.test/resource", {
        endpointLabel: "/resource",
      }),
    ).rejects.toSatisfy((error: unknown) => {
      expect((error as HttpError).message).toBe(
        "Network error. Please check your connection.",
      )
      expect((error as HttpError).endpointLabel).toBe("/resource")
      return true
    })
  })

  it("maps an already-aborted caller signal to HttpError", async () => {
    const controller = new AbortController()
    controller.abort()

    vi.stubGlobal("fetch", mockFetchThatRejectsOnAbort())

    await expect(
      httpFetch("https://api.test/resource", { signal: controller.signal }),
    ).rejects.toSatisfy((error: unknown) => {
      expect((error as HttpError).message).toBe("Request was cancelled.")
      return true
    })
  })

  it("aborts when the timeout elapses", async () => {
    vi.useFakeTimers()
    vi.stubGlobal("fetch", mockFetchThatRejectsOnAbort())

    const assertion = expect(
      httpFetch("https://api.test/slow", { timeoutMs: 50 }),
    ).rejects.toSatisfy((error: unknown) => {
      expect((error as HttpError).message).toBe("Request was cancelled.")
      return true
    })

    await vi.advanceTimersByTimeAsync(50)
    await assertion
  })

  it("passes request init through to fetch", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)

    await httpFetch("https://api.test/resource", {
      method: "POST",
      body: JSON.stringify({ prompt: "hello" }),
      headers: { "Content-Type": "application/json" },
    })

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.test/resource",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ prompt: "hello" }),
        headers: { "Content-Type": "application/json" },
        signal: expect.any(AbortSignal),
      }),
    )
  })
})
