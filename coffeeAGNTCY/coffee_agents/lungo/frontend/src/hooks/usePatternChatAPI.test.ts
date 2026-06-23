/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { act, renderHook } from "@testing-library/react"
import {
  PatternChatNotFoundError,
  PatternChatTransportError,
  usePatternChatAPI,
} from "./usePatternChatAPI"

const originalFetch = globalThis.fetch
const encoder = new TextEncoder()

afterEach(() => {
  globalThis.fetch = originalFetch
  vi.restoreAllMocks()
})

beforeEach(() => {
  vi.stubEnv("VITE_AGENTIC_WORKFLOWS_API_URL", "http://test-host:1234")
})

const streamingResponse = (status: number, chunks: string[]): Response => {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return new Response(stream, {
    status,
    headers: { "Content-Type": "application/x-ndjson" },
  })
}

const jsonResponse = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })

const mockFetch = (impl: () => Response | Promise<Response>) => {
  const fn = vi.fn(async () => impl())
  globalThis.fetch = fn as unknown as typeof fetch
  return fn
}

const makeCallbacks = () => ({
  onChunk: vi.fn<(text: string) => void>(),
  onDone: vi.fn<() => void>(),
  onError: vi.fn<(err: Error) => void>(),
})

const REQ = {
  patternName: "Feedback Loop",
  sessionId: "session://00000000-0000-4000-a000-000000000001",
  message: "What is it?",
} as const

describe("usePatternChatAPI", () => {
  it("delivers each response chunk in order, then onDone", async () => {
    mockFetch(() =>
      streamingResponse(200, [
        '{"response": "Hello"}\n',
        '{"response": " world"}\n',
        '{"done": true}\n',
      ]),
    )
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    expect(cb.onChunk).toHaveBeenCalledTimes(2)
    expect(cb.onChunk).toHaveBeenNthCalledWith(1, "Hello")
    expect(cb.onChunk).toHaveBeenNthCalledWith(2, " world")
    expect(cb.onDone).toHaveBeenCalledOnce()
    expect(cb.onError).not.toHaveBeenCalled()
  })

  it("handles frames split across read() boundaries", async () => {
    mockFetch(() =>
      streamingResponse(200, [
        '{"response": "He',
        'llo"}\n{"resp',
        'onse": " world"}\n{"done": true}\n',
      ]),
    )
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    expect(cb.onChunk.mock.calls.map((c) => c[0])).toEqual(["Hello", " world"])
    expect(cb.onDone).toHaveBeenCalledOnce()
  })

  it("surfaces an in-stream error frame via onError and stops", async () => {
    mockFetch(() =>
      streamingResponse(200, [
        '{"response": "partial"}\n',
        '{"error": "model timed out"}\n',
        '{"response": "after-error"}\n',
      ]),
    )
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    expect(cb.onChunk).toHaveBeenCalledExactlyOnceWith("partial")
    expect(cb.onError).toHaveBeenCalledOnce()
    expect(cb.onError.mock.calls[0]![0].message).toBe("model timed out")
    expect(cb.onDone).not.toHaveBeenCalled()
  })

  it("surfaces HTTP 404 as PatternChatNotFoundError", async () => {
    mockFetch(() => jsonResponse(404, { detail: "missing" }))
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    expect(cb.onError).toHaveBeenCalledOnce()
    expect(cb.onError.mock.calls[0]![0]).toBeInstanceOf(
      PatternChatNotFoundError,
    )
    expect(cb.onChunk).not.toHaveBeenCalled()
    expect(cb.onDone).not.toHaveBeenCalled()
  })

  it("surfaces other non-OK statuses as PatternChatTransportError", async () => {
    mockFetch(() => jsonResponse(503, { detail: "down" }))
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    const errArg = cb.onError.mock.calls[0]![0]
    expect(errArg).toBeInstanceOf(PatternChatTransportError)
    expect(errArg.message).toContain("HTTP 503")
  })

  it("flags a stream that closes without a done frame", async () => {
    mockFetch(() => streamingResponse(200, ['{"response": "partial"}\n']))
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    expect(cb.onChunk).toHaveBeenCalledExactlyOnceWith("partial")
    expect(cb.onDone).not.toHaveBeenCalled()
    expect(cb.onError).toHaveBeenCalledOnce()
    expect(cb.onError.mock.calls[0]![0]).toBeInstanceOf(
      PatternChatTransportError,
    )
  })

  it("URL-encodes the pattern name and posts JSON body", async () => {
    const fn = mockFetch(() => streamingResponse(200, ['{"done": true}\n']))
    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    await act(async () => {
      await result.current.sendPatternMessage(REQ, cb)
    })

    const firstCall = fn.mock.calls[0] as unknown as [
      string,
      { method?: string; body?: string },
    ]
    expect(firstCall[0]).toBe(
      "http://test-host:1234/patterns/Feedback%20Loop/chat",
    )
    expect(firstCall[1]?.method).toBe("POST")
    expect(firstCall[1]?.body).toBe(
      JSON.stringify({
        session_id: "session://00000000-0000-4000-a000-000000000001",
        message: "What is it?",
      }),
    )
  })

  it("cancel() aborts an in-flight request", async () => {
    let captured: AbortSignal | undefined
    globalThis.fetch = vi.fn(
      async (
        _url: unknown,
        init?: { signal?: AbortSignal | null },
      ): Promise<Response> => {
        captured = init?.signal ?? undefined
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            captured?.addEventListener("abort", () => {
              controller.error(new DOMException("Aborted", "AbortError"))
            })
          },
        })
        return new Response(stream, {
          status: 200,
          headers: { "Content-Type": "application/x-ndjson" },
        })
      },
    ) as unknown as typeof fetch

    const { result } = renderHook(() => usePatternChatAPI())
    const cb = makeCallbacks()

    let inflight: Promise<void> | null = null
    act(() => {
      inflight = result.current.sendPatternMessage(REQ, cb)
    })

    await new Promise<void>((resolve) => setTimeout(resolve, 0))
    expect(captured).toBeDefined()

    act(() => {
      result.current.cancel()
    })

    expect(captured?.aborted).toBe(true)
    await inflight
    expect(cb.onError).not.toHaveBeenCalled()
    expect(cb.onDone).not.toHaveBeenCalled()
    expect(cb.onChunk).not.toHaveBeenCalled()
  })
})
