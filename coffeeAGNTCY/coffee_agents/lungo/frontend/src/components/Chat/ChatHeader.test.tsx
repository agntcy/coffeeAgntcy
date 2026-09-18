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
  it("does not render the clear control without onClearConversation", () => {
    renderHeader()

    expect(
      screen.queryByRole("button", { name: "Clear conversation" }),
    ).not.toBeInTheDocument()
  })

  it("renders a clear button with tooltip and aria-label", async () => {
    const onClearConversation = vi.fn()

    renderHeader({ onClearConversation })

    const button = screen.getByRole("button", { name: "Clear conversation" })
    fireEvent.mouseOver(button)
    expect(
      await screen.findByRole("tooltip", { name: "Clear conversation" }),
    ).toBeInTheDocument()
  })

  it("invokes onClearConversation when the clear button is clicked", () => {
    const onClearConversation = vi.fn()

    renderHeader({ onClearConversation })

    fireEvent.click(screen.getByRole("button", { name: "Clear conversation" }))
    expect(onClearConversation).toHaveBeenCalledOnce()
  })
})
