/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  HttpError,
  isHttpError,
  parseHttpError,
  parseHttpErrorFromResponse,
} from "@/api/http"

function makeResponse(
  body: string,
  init: { status?: number; statusText?: string; contentType?: string } = {},
): Response {
  const status = init.status ?? 500
  const headers = new Headers()
  if (init.contentType) {
    headers.set("content-type", init.contentType)
  }
  return new Response(body, {
    status,
    statusText: init.statusText ?? "Internal Server Error",
    headers,
  })
}

describe("parseHttpError", () => {
  it("returns the same HttpError instance when already parsed", () => {
    const original = new HttpError("already parsed", { status: 400 })
    expect(parseHttpError(original)).toBe(original)
  })

  it("maps abort errors to a cancellation message", () => {
    const error = new DOMException("The operation was aborted.", "AbortError")
    const parsed = parseHttpError(error)
    expect(parsed.message).toBe("Request was cancelled.")
    expect(parsed.cause).toBe(error)
  })

  it("maps network TypeError to a connection message", () => {
    const error = new TypeError("Failed to fetch")
    const parsed = parseHttpError(error)
    expect(parsed.message).toBe("Network error. Please check your connection.")
    expect(parsed.cause).toBe(error)
  })

  it("uses Error.message for generic errors", () => {
    const parsed = parseHttpError(new Error("Something broke"))
    expect(parsed.message).toBe("Something broke")
  })

  it("falls back to a generic message for unknown values", () => {
    const parsed = parseHttpError(null)
    expect(parsed.message).toBe(
      "Sorry, something went wrong. Please try again later.",
    )
  })

  it("preserves endpointLabel metadata", () => {
    const parsed = parseHttpError(new TypeError("Failed to fetch"), {
      endpointLabel: "/api/workflows",
    })
    expect(parsed.endpointLabel).toBe("/api/workflows")
  })
})

describe("parseHttpErrorFromResponse", () => {
  it("parses FastAPI string detail from JSON responses", async () => {
    const response = makeResponse(
      JSON.stringify({ detail: "Catalog unavailable" }),
      { status: 503, contentType: "application/json" },
    )
    const parsed = await parseHttpErrorFromResponse(response)
    expect(parsed.status).toBe(503)
    expect(parsed.message).toBe("Catalog unavailable")
  })

  it("parses FastAPI validation arrays from JSON responses", async () => {
    const response = makeResponse(
      JSON.stringify({
        detail: [
          {
            type: "value_error",
            loc: ["body", "prompt"],
            msg: "Prompt is required",
          },
          {
            type: "value_error",
            loc: ["body", "session_id"],
            msg: "Session is required",
          },
        ],
      }),
      { status: 422, contentType: "application/json" },
    )
    const parsed = await parseHttpErrorFromResponse(response)
    expect(parsed.message).toBe(
      "prompt: Prompt is required; session_id: Session is required",
    )
  })

  it("strips HTML from non-JSON error pages", async () => {
    const response = makeResponse(
      "<html><body><h1>Gateway Timeout</h1></body></html>",
      { status: 504, contentType: "text/html" },
    )
    const parsed = await parseHttpErrorFromResponse(response)
    expect(parsed.message).toBe("Gateway Timeout")
  })

  it("falls back to raw text when JSON header is invalid", async () => {
    const response = makeResponse("not-json", {
      status: 500,
      contentType: "application/json",
    })
    const parsed = await parseHttpErrorFromResponse(response)
    expect(parsed.message).toBe("not-json")
  })

  it("uses the default HTTP message for empty bodies", async () => {
    const response = makeResponse("", {
      status: 502,
      statusText: "Bad Gateway",
    })
    const parsed = await parseHttpErrorFromResponse(response)
    expect(parsed.message).toBe("HTTP 502: Bad Gateway")
  })

  it("preserves endpointLabel metadata", async () => {
    const response = makeResponse(JSON.stringify({ detail: "nope" }), {
      status: 400,
      contentType: "application/json",
    })
    const parsed = await parseHttpErrorFromResponse(response, {
      endpointLabel: "/api/catalog",
    })
    expect(parsed.endpointLabel).toBe("/api/catalog")
  })
})

describe("HttpError", () => {
  it("identifies HttpError instances", () => {
    const error = new HttpError("boom", { status: 500 })
    expect(isHttpError(error)).toBe(true)
    expect(isHttpError(new Error("boom"))).toBe(false)
  })
})
