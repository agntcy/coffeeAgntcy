/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen } from "@testing-library/react"
import type { ComponentProps } from "react"
import { describe, expect, it, vi } from "vitest"
import ErrorFallback from "./ErrorFallback"

const renderFallback = (props: ComponentProps<typeof ErrorFallback>) =>
  render(
    <ThemeProvider>
      <ErrorFallback {...props} />
    </ThemeProvider>,
  )

describe("ErrorFallback", () => {
  it("renders an accessible alert with title and error message", () => {
    renderFallback({
      error: new Error("Graph render failed"),
      actionTitle: "Try again",
      onAction: vi.fn(),
      title: "Graph unavailable",
    })

    expect(screen.getByRole("alert")).toBeInTheDocument()
    expect(screen.getByText("Graph unavailable")).toBeInTheDocument()
    expect(screen.getByText("Graph render failed")).toBeInTheDocument()
  })

  it("invokes the action callback when the button is clicked", () => {
    const onAction = vi.fn()

    renderFallback({
      error: new Error("Boom"),
      actionTitle: "Try again",
      onAction,
    })

    fireEvent.click(screen.getByRole("button", { name: "Try again" }))
    expect(onAction).toHaveBeenCalledOnce()
  })
})
