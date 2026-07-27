/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it, vi } from "vitest"
import { fetchJson, HttpError, isHttpError } from "@/api/http"

describe("fetchJson", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("parses JSON for successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ id: "badge-1" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    )

    await expect(
      fetchJson<{ id: string }>("https://api.test/badge"),
    ).resolves.toEqual({ id: "badge-1" })
  })

  it("throws HttpError for non-OK responses with FastAPI detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Badge not found" }), {
          status: 404,
          headers: { "content-type": "application/json" },
        }),
      ),
    )

    await expect(
      fetchJson("https://api.test/badge", { endpointLabel: "/identity/badge" }),
    ).rejects.toSatisfy((error: unknown) => {
      expect(isHttpError(error)).toBe(true)
      expect((error as HttpError).status).toBe(404)
      expect((error as HttpError).message).toBe("Badge not found")
      expect((error as HttpError).endpointLabel).toBe("/identity/badge")
      return true
    })
  })

  it("sends Content-Type application/json when a body is provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    )
    vi.stubGlobal("fetch", fetchMock)

    await fetchJson("https://api.test/agent/prompt", {
      method: "POST",
      body: JSON.stringify({ prompt: "hello" }),
    })

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.test/agent/prompt",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Accept: "application/json",
          "Content-Type": "application/json",
        }),
      }),
    )
  })

  it("maps abort errors to HttpError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new DOMException("Aborted", "AbortError")),
    )

    await expect(
      fetchJson("https://api.test/badge", { timeoutMs: 5 }),
    ).rejects.toSatisfy((error: unknown) => {
      expect((error as HttpError).message).toBe("Request was cancelled.")
      return true
    })
  })
})
