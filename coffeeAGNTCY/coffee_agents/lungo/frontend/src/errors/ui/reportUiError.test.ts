/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it, vi } from "vitest"
import { useErrorNotificationStore } from "./errorNotificationStore"

const mockLoggerError = vi.fn()
const mockUnsafeLoggerError = vi.fn()

vi.mock("@/utils/logger", () => ({
  logger: {
    error: mockLoggerError,
  },
  unsafeLogger: {
    error: mockUnsafeLoggerError,
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

const { reportUiError } = await import("./reportUiError")

describe("reportUiError", () => {
  beforeEach(() => {
    useErrorNotificationStore.setState({ notifications: [] })
    mockLoggerError.mockReset()
    mockUnsafeLoggerError.mockReset()
    envState.dev = true
  })

  it("pushes a notification with a default title", () => {
    const id = reportUiError({ message: "Graph failed to load" })

    expect(id).toBeTruthy()
    expect(useErrorNotificationStore.getState().notifications).toEqual([
      expect.objectContaining({
        id,
        title: "Something went wrong",
        message: "Graph failed to load",
        severity: "error",
      }),
    ])
  })

  it("logs through logger in development", () => {
    reportUiError({
      title: "Render error",
      message: "Component crashed",
      source: "MainArea",
    })

    expect(mockLoggerError).toHaveBeenCalledOnce()
    expect(mockUnsafeLoggerError).not.toHaveBeenCalled()
  })

  it("logs through unsafeLogger in production", () => {
    envState.dev = false

    reportUiError({ message: "Component crashed" })

    expect(mockUnsafeLoggerError).toHaveBeenCalledOnce()
    expect(mockLoggerError).not.toHaveBeenCalled()
  })

  it("skips the notification banner when notify is false", () => {
    const id = reportUiError({
      message: "Boundary caught a render error",
      notify: false,
    })

    expect(id).toBe("")
    expect(useErrorNotificationStore.getState().notifications).toEqual([])
    expect(mockLoggerError).toHaveBeenCalledOnce()
  })
})
