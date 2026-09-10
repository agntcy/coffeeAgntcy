/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Icons, ThemeProvider } from "@open-ui-kit/core"
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

  it("renders a compact clear button with tooltip, aria-label, and OUK delete icon", async () => {
    const onClearConversation = vi.fn()
    const { container: deleteIconContainer } = render(
      <ThemeProvider>
        <Icons.Delete />
      </ThemeProvider>,
    )
    const expectedGlyph = deleteIconContainer.querySelector("svg")?.innerHTML

    renderHeader({ onClearConversation })

    const button = screen.getByRole("button", { name: "Clear conversation" })
    expect(button).toHaveClass("MuiIconButton-sizeSmall")
    expect(button.querySelector("svg")?.innerHTML).toBe(expectedGlyph)

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
