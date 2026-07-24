/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it, vi } from "vitest"
import {
  consumeJsonObjectsFromBuffer,
  consumeNdjsonLines,
} from "@/api/http/ndjsonParsing"
import { fetchNdjsonStream, HttpError } from "@/api/http"

describe("ndjsonParsing", () => {
  it("consumes newline-delimited JSON lines", () => {
    const seen: unknown[] = []
    const remainder = consumeNdjsonLines(
      '{"a":1}\n{"b":2}\n{"c":',
      (parsed) => {
        seen.push(parsed)
      },
    )

    expect(seen).toEqual([{ a: 1 }, { b: 2 }])
    expect(remainder).toBe('{"c":')
  })

  it("consumes concatenated JSON objects from a buffer", () => {
    const seen: unknown[] = []
    const remainder = consumeJsonObjectsFromBuffer(
      '{"a":1}{"b":2}{"c":',
      (parsed) => {
        seen.push(parsed)
      },
    )

    expect(seen).toEqual([{ a: 1 }, { b: 2 }])
    expect(remainder).toBe('{"c":')
  })
})

describe("fetchNdjsonStream", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("reads NDJSON lines from a successful stream", async () => {
    const encoder = new TextEncoder()
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('{"id":1}\n{"id":2}\n'))
        controller.close()
      },
    })

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(body, {
          status: 200,
          headers: { "content-type": "application/x-ndjson" },
        }),
      ),
    )

    const seen: unknown[] = []
    await fetchNdjsonStream("https://api.test/stream", {
      method: "POST",
      endpointLabel: "/agent/prompt/stream",
      onLine: (parsed) => {
        seen.push(parsed)
      },
    })

    expect(seen).toEqual([{ id: 1 }, { id: 2 }])
  })

  it("throws HttpError for non-OK responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Bad prompt" }), {
          status: 400,
          headers: { "content-type": "application/json" },
        }),
      ),
    )

    await expect(
      fetchNdjsonStream("https://api.test/stream", {
        method: "POST",
        endpointLabel: "/agent/prompt/stream",
        onLine: () => {},
      }),
    ).rejects.toBeInstanceOf(HttpError)
  })

  it("cancels the response body reader when onLine returns stop", async () => {
    const encoder = new TextEncoder()
    let bodyCancelled = false
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('{"id":1}\n{"id":2}\n'))
      },
      cancel() {
        bodyCancelled = true
      },
    })

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(body, {
          status: 200,
          headers: { "content-type": "application/x-ndjson" },
        }),
      ),
    )

    const seen: unknown[] = []
    await fetchNdjsonStream("https://api.test/stream", {
      method: "POST",
      endpointLabel: "/agent/prompt/stream",
      onLine: (parsed) => {
        seen.push(parsed)
        return "stop"
      },
    })

    expect(seen).toEqual([{ id: 1 }])
    expect(bodyCancelled).toBe(true)
  })
})
