/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { HttpError, ndjsonStreamUserMessage } from "@/api/http"

describe("ndjsonStreamUserMessage", () => {
  it("includes server detail for 4xx HttpError responses", () => {
    const message = ndjsonStreamUserMessage(
      new HttpError("Prompt is required", { status: 422 }),
    )

    expect(message).toBe("HTTP 422 - Prompt is required")
  })

  it("uses generic copy for 5xx HttpError responses", () => {
    const message = ndjsonStreamUserMessage(
      new HttpError("Internal server error", { status: 500 }),
    )

    expect(message).toBe("Sorry, something went wrong. Please try again later.")
  })

  it("uses short generic copy when requested", () => {
    const message = ndjsonStreamUserMessage(new Error("network down"), "short")

    expect(message).toBe("Sorry, something went wrong. Please try again.")
  })

  it("uses default generic copy for non-HttpError failures", () => {
    const message = ndjsonStreamUserMessage(new TypeError("Failed to fetch"))

    expect(message).toBe("Sorry, something went wrong. Please try again later.")
  })
})
