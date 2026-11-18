/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { act, renderHook } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { useAppChatState } from "./useAppChatState"

const summary = (name: string): WorkflowSummary => ({
  name,
  pattern: "group_messaging",
  pattern_category: "supply",
  use_case: "order",
  scenario: "demo",
  supports_sse: true,
  supports_streaming: false,
  chat_api_target: "exchange",
})

describe("useAppChatState", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("clears the in-progress reply flags when the workflow name changes", () => {
    const { result, rerender } = renderHook(
      ({ name }: { name: string }) =>
        useAppChatState({ selectedWorkflowSummary: summary(name) }),
      { initialProps: { name: "alpha" } },
    )

    act(() => {
      result.current.handleUserInput("hello")
    })
    expect(result.current.buttonClicked).toBe(true)

    rerender({ name: "beta" })
    expect(result.current.buttonClicked).toBe(false)
    expect(result.current.aiReplied).toBe(false)
  })
})
