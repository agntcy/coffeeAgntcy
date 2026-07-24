/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it, vi } from "vitest"
import { HttpError } from "@/api/http"
import { useErrorNotificationStore } from "@/errors/ui/errorNotificationStore"

const mockLoggerError = vi.fn()
const mockUnsafeLoggerError = vi.fn()

vi.mock("@/utils/logger", () => ({
  logger: {
    error: mockLoggerError,
    apiError: vi.fn(),
  },
  unsafeLogger: {
    error: mockUnsafeLoggerError,
    apiError: vi.fn(),
  },
}))

const envState = { dev: true }

vi.mock("@/utils/env", () => ({
  env: {
    get dev() {
      return envState.dev
    },
  },
}))

const { reportRequestError } = await import("./reportRequestError")

describe("reportRequestError", () => {
  beforeEach(() => {
    mockLoggerError.mockReset()
    mockUnsafeLoggerError.mockReset()
    envState.dev = true
    useErrorNotificationStore.setState({ notifications: [] })
  })

  it("returns an existing HttpError unchanged", () => {
    const original = new HttpError("Catalog unavailable", {
      status: 503,
      endpointLabel: "/api/catalog",
    })

    const result = reportRequestError("/api/catalog", original)

    expect(result).toBe(original)
    expect(mockLoggerError).toHaveBeenCalledWith(
      "API Error - /api/catalog",
      expect.objectContaining({
        message: "Catalog unavailable",
        status: 503,
        endpointLabel: "/api/catalog",
      }),
    )
  })

  it("logs HttpError.endpointLabel when it differs from the passed label", () => {
    const error = new HttpError("Not found", {
      status: 404,
      endpointLabel: "/identity-apps/shipping-agent/badge",
    })

    reportRequestError("/identity-apps/fallback/badge", error)

    expect(mockLoggerError).toHaveBeenCalledWith(
      "API Error - /identity-apps/shipping-agent/badge",
      expect.objectContaining({
        endpointLabel: "/identity-apps/shipping-agent/badge",
      }),
    )
  })

  it("normalizes unknown errors to HttpError with endpointLabel metadata", () => {
    const result = reportRequestError(
      "/api/workflows",
      new TypeError("Failed to fetch"),
    )

    expect(result).toBeInstanceOf(HttpError)
    expect(result.endpointLabel).toBe("/api/workflows")
    expect(result.message).toBe("Network error. Please check your connection.")
  })

  it("uses logger in development", () => {
    envState.dev = true

    reportRequestError("/api/test", new Error("boom"))

    expect(mockLoggerError).toHaveBeenCalledOnce()
    expect(mockUnsafeLoggerError).not.toHaveBeenCalled()
  })

  it("uses unsafeLogger in production", () => {
    envState.dev = false

    reportRequestError("/api/test", new Error("boom"))

    expect(mockUnsafeLoggerError).toHaveBeenCalledOnce()
    expect(mockLoggerError).not.toHaveBeenCalled()
  })

  it("includes optional context and userMessage in the log payload", () => {
    reportRequestError("/api/test", new HttpError("nope", { status: 400 }), {
      userMessage: "Could not load menu",
      pattern: "auction",
    })

    expect(mockLoggerError).toHaveBeenCalledWith(
      "API Error - /api/test",
      expect.objectContaining({
        userMessage: "Could not load menu",
        pattern: "auction",
        status: 400,
      }),
    )
  })

  it("pushes a user-visible notification when userMessage is provided", () => {
    reportRequestError("/api/catalog", new HttpError("nope", { status: 503 }), {
      userMessage: "Menu is unavailable",
    })

    expect(useErrorNotificationStore.getState().notifications).toEqual([
      expect.objectContaining({
        title: "Request failed",
        message: "Menu is unavailable",
        source: "/api/catalog",
      }),
    ])
  })

  it("fills endpointLabel on HttpError when missing", () => {
    const original = new HttpError("Menu unavailable", { status: 500 })
    const result = reportRequestError("/api/catalog", original)

    expect(result).toBeInstanceOf(HttpError)
    expect(result).not.toBe(original)
    expect(result.endpointLabel).toBe("/api/catalog")
    expect(result.message).toBe("Menu unavailable")
  })
})
