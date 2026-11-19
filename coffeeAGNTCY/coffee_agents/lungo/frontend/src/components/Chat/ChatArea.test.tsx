/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { useState } from "react"
import { describe, expect, it, vi } from "vitest"

import ChatArea from "./ChatArea"
import type { UseSuggestedPromptsResult } from "./prompts"

const promptsState = vi.hoisted(() => ({
  current: {
    categories: [
      { name: "Orders", prompts: [{ prompt: "Brew", description: "" }] },
    ],
    isLoading: false,
    isUnavailable: false,
    unavailableMessage: null,
  } as UseSuggestedPromptsResult,
}))

vi.mock("./prompts/useSuggestedPrompts", () => ({
  useSuggestedPrompts: () => promptsState.current,
}))

vi.mock("@/utils/chatScroll", () => ({
  useScrollPanelOnContentResize: () => {},
}))

function deferred() {
  let release: () => void = () => {}
  const promise = new Promise<void>((resolve) => {
    release = resolve
  })
  return { promise, release: () => release() }
}

function Harness({
  pending,
  onClear,
}: {
  pending: Promise<void>
  onClear: () => void
}) {
  const [currentUserMessage, setCurrentUserMessage] = useState("")

  return (
    <ThemeProvider>
      <ChatArea
        isBottomLayout
        fillHeight={false}
        currentUserMessage={currentUserMessage}
        suggestedPromptsRequest={{
          url: "https://example.test/suggested-prompts",
          endpointLabel: "suggested prompts",
        }}
        onSendPrompt={async () => {
          setCurrentUserMessage("Brew a coffee")
          await pending
        }}
        onClearConversation={() => {
          setCurrentUserMessage("")
          onClear()
        }}
      />
    </ThemeProvider>
  )
}

describe("ChatArea", () => {
  it("re-enables suggested prompts when a prompt is cleared before it finishes", async () => {
    const request = deferred()
    const onClear = vi.fn()
    render(<Harness pending={request.promise} onClear={onClear} />)

    fireEvent.change(
      screen.getByRole("textbox", { name: "Message to agents" }),
      {
        target: { value: "Brew a coffee" },
      },
    )
    fireEvent.click(screen.getByRole("button", { name: "Send" }))

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Suggested Prompts" }),
      ).toHaveAttribute("aria-disabled", "true")
    })

    fireEvent.click(screen.getByRole("button", { name: "Clear conversation" }))

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Suggested Prompts" }),
      ).not.toHaveAttribute("aria-disabled")
    })
    expect(onClear).toHaveBeenCalledOnce()
    expect(
      screen.getByRole("textbox", { name: "Message to agents" }),
    ).not.toBeDisabled()

    request.release()
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Suggested Prompts" }),
      ).not.toHaveAttribute("aria-disabled")
    })
  })
})
