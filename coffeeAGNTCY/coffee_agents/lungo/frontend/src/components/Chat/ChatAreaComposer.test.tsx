/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { render, screen } from "@testing-library/react"
import type { ComponentProps } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import ChatAreaComposer from "./ChatAreaComposer"
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

type ComposerProps = ComponentProps<typeof ChatAreaComposer>

const renderComposer = (props: Partial<ComposerProps> = {}) =>
  render(
    <ThemeProvider>
      <ChatAreaComposer
        suggestedPromptsRequest={{
          url: "https://example.test/suggested-prompts",
          endpointLabel: "suggested prompts",
        }}
        onSuggestedPromptSelect={vi.fn()}
        content="Brew a coffee"
        setContent={vi.fn()}
        loading={false}
        onSend={vi.fn()}
        onKeyDown={vi.fn()}
        {...props}
      />
    </ThemeProvider>,
  )

const getControls = () => ({
  input: screen.getByLabelText("Message to agents"),
  send: screen.getByRole("button", { name: /send/i }),
  promptsTrigger: screen.getByRole("button", { name: /suggested prompts/i }),
})

describe("ChatAreaComposer", () => {
  beforeEach(() => {
    promptsState.current = {
      categories: [
        { name: "Orders", prompts: [{ prompt: "Brew", description: "" }] },
      ],
      isLoading: false,
      isUnavailable: false,
      unavailableMessage: null,
    }
  })

  it("enables all three controls when the endpoint is reachable", () => {
    renderComposer()

    const { input, send, promptsTrigger } = getControls()
    expect(input).toBeEnabled()
    expect(send).toBeEnabled()
    expect(promptsTrigger).not.toHaveAttribute("aria-disabled")
  })

  it("disables all three controls when the endpoint is unavailable", () => {
    renderComposer({ endpointUnavailable: true })

    const { input, send, promptsTrigger } = getControls()
    expect(input).toBeDisabled()
    expect(send).toBeDisabled()
    expect(promptsTrigger).toHaveAttribute("aria-disabled", "true")
  })

  it("disables all three controls while a message is in flight", () => {
    renderComposer({ loading: true })

    const { input, send, promptsTrigger } = getControls()
    expect(input).toBeDisabled()
    expect(send).toBeDisabled()
    expect(promptsTrigger).toHaveAttribute("aria-disabled", "true")
  })

  it("keeps the prompts trigger clickable when prompts are the failing endpoint", () => {
    promptsState.current = {
      categories: [],
      isLoading: false,
      isUnavailable: true,
      unavailableMessage: "Request failed",
    }

    renderComposer()

    const { input, send, promptsTrigger } = getControls()
    expect(input).toBeDisabled()
    expect(send).toBeDisabled()
    expect(promptsTrigger).not.toHaveAttribute("aria-disabled")
  })

  it("omits the prompts trigger when no prompts request applies", () => {
    renderComposer({ suggestedPromptsRequest: null })

    expect(
      screen.queryByRole("button", { name: /suggested prompts/i }),
    ).not.toBeInTheDocument()
    expect(screen.getByLabelText("Message to agents")).toBeEnabled()
  })
})
