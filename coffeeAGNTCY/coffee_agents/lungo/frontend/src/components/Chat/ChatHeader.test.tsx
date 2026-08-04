/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen } from "@testing-library/react"
import type { ComponentProps } from "react"
import { describe, expect, it, vi } from "vitest"
import ChatHeader from "./ChatHeader"

const renderHeader = (props: ComponentProps<typeof ChatHeader> = {}) =>
  render(
    <ThemeProvider>
      <ChatHeader {...props} />
    </ThemeProvider>,
  )

describe("ChatHeader", () => {
  it("renders no button when onClearConversation is not provided", () => {
    renderHeader()

    expect(
      screen.queryByRole("button", { name: "Clear conversation" }),
    ).not.toBeInTheDocument()
  })

  it("invokes onClearConversation when the clear button is clicked", () => {
    const onClearConversation = vi.fn()

    renderHeader({ onClearConversation })

    fireEvent.click(screen.getByRole("button", { name: "Clear conversation" }))
    expect(onClearConversation).toHaveBeenCalledOnce()
  })

  it("gives the clear conversation button a >=44x44 touch target", () => {
    renderHeader({ onClearConversation: vi.fn() })

    const button = screen.getByRole("button", { name: "Clear conversation" })
    const { width, height } = getComputedStyle(button)

    expect(parseFloat(width)).toBeGreaterThanOrEqual(44)
    expect(parseFloat(height)).toBeGreaterThanOrEqual(44)
  })
})
