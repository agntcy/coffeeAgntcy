/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import ErrorBoundary from "./ErrorBoundary"
import { useErrorNotificationStore } from "./errorNotificationStore"

const mockReportUiError = vi.fn()

vi.mock("./reportUiError", () => ({
  reportUiError: (...args: unknown[]) => mockReportUiError(...args),
}))

type ThrowingChildProps = {
  shouldThrow: boolean
  message?: string
}

const ThrowingChild = ({
  shouldThrow,
  message = "Render exploded",
}: ThrowingChildProps) => {
  if (shouldThrow) {
    throw new Error(message)
  }

  return <div>Child recovered</div>
}

const renderBoundary = (
  ui: React.ReactElement,
  boundaryProps?: Omit<React.ComponentProps<typeof ErrorBoundary>, "children">,
) =>
  render(
    <ThemeProvider>
      <ErrorBoundary {...boundaryProps}>{ui}</ErrorBoundary>
    </ThemeProvider>,
  )

describe("ErrorBoundary", () => {
  beforeEach(() => {
    mockReportUiError.mockReset()
    useErrorNotificationStore.setState({ notifications: [] })
  })

  it("renders children when no error occurs", () => {
    renderBoundary(<ThrowingChild shouldThrow={false} />)

    expect(screen.getByText("Child recovered")).toBeInTheDocument()
  })

  it("renders OUK fallback when a child throws", () => {
    renderBoundary(<ThrowingChild shouldThrow />, {
      fallbackTitle: "Application error",
    })

    expect(screen.getByRole("alert")).toBeInTheDocument()
    expect(screen.getByText("Application error")).toBeInTheDocument()
    expect(screen.getByText("Render exploded")).toBeInTheDocument()
  })

  it("logs through reportUiError without pushing a global banner", () => {
    renderBoundary(<ThrowingChild shouldThrow message="Boundary boom" />, {
      source: "TestBoundary",
      fallbackTitle: "Application error",
    })

    expect(mockReportUiError).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Application error",
        message: "Boundary boom",
        source: "TestBoundary",
        notify: false,
      }),
    )
    expect(useErrorNotificationStore.getState().notifications).toEqual([])
  })

  it("resets and re-renders children when Try again is clicked", () => {
    const { rerender } = render(
      <ThemeProvider>
        <ErrorBoundary>
          <ThrowingChild shouldThrow message="Still broken" />
        </ErrorBoundary>
      </ThemeProvider>,
    )

    expect(screen.getByText("Still broken")).toBeInTheDocument()

    rerender(
      <ThemeProvider>
        <ErrorBoundary>
          <ThrowingChild shouldThrow={false} />
        </ErrorBoundary>
      </ThemeProvider>,
    )

    fireEvent.click(screen.getByRole("button", { name: "Try again" }))

    expect(screen.getByText("Child recovered")).toBeInTheDocument()
  })

  it("reloads the page when useReload is enabled", () => {
    const reload = vi.fn()
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { reload },
    })

    renderBoundary(<ThrowingChild shouldThrow />, { useReload: true })

    fireEvent.click(screen.getByRole("button", { name: "Reload page" }))
    expect(reload).toHaveBeenCalledOnce()
  })
})
