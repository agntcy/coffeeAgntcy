/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it, vi } from "vitest"
import { fetchSse, HttpError, isHttpError } from "@/api/http"

describe("fetchSse", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("parses SSE data lines and invokes onEvent", async () => {
    const encoder = new TextEncoder()
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode('data: {"id":1}\n\ndata: {"id":2}\n\n'),
        )
        controller.close()
      },
    })

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(body, {
          status: 200,
          headers: { "content-type": "text/event-stream" },
        }),
      ),
    )

    const events: unknown[] = []
    fetchSse<{ id: number }>("https://api.test/events/stream", {
      endpointLabel: "/events/stream",
      onEvent: (event) => {
        events.push(event)
      },
    })

    await vi.waitFor(() => {
      expect(events).toEqual([{ id: 1 }, { id: 2 }])
    })

    expect(fetch).toHaveBeenCalledWith(
      "https://api.test/events/stream",
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: "text/event-stream",
        }),
        cache: "no-store",
      }),
    )
  })

  it("invokes onError for non-OK responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Forbidden" }), {
          status: 403,
          headers: { "content-type": "application/json" },
        }),
      ),
    )

    let error: unknown
    fetchSse("https://api.test/events/stream", {
      endpointLabel: "/events/stream",
      onEvent: () => {},
      onError: (err) => {
        error = err
      },
    })

    await vi.waitFor(() => {
      expect(error).toBeDefined()
    })

    expect(isHttpError(error)).toBe(true)
    expect((error as HttpError).status).toBe(403)
  })

  it("returns close() that aborts the underlying fetch", async () => {
    let aborted = false
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((_url, init) => {
        init?.signal?.addEventListener("abort", () => {
          aborted = true
        })
        return new Promise<Response>(() => {})
      }),
    )

    const close = fetchSse("https://api.test/events/stream", {
      endpointLabel: "/events/stream",
      onEvent: () => {},
    })

    close()

    await vi.waitFor(() => {
      expect(aborted).toBe(true)
    })
  })
})
