/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { act, renderHook } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { CanvasMode } from "@/types/patternDoc"
import { useAppPatternReference } from "./useAppPatternReference"

vi.mock("@/utils/agenticWorkflowsApi", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/utils/agenticWorkflowsApi")>()
  return {
    ...actual,
    fetchWorkflowDocumentation: vi.fn(() => new Promise(() => {})),
  }
})

vi.mock("@/errors/request", () => ({
  reportRequestError: vi.fn(),
}))

describe("useAppPatternReference", () => {
  it("shows loading as soon as a reference pattern is selected", () => {
    const { result } = renderHook(() => useAppPatternReference())

    expect(result.current.canvasMode).toBe(CanvasMode.WORKFLOW)
    expect(result.current.patternDocState.status).toBe("idle")

    act(() => {
      result.current.selectReferencePattern("auction")
    })

    expect(result.current.canvasMode).toBe(CanvasMode.PATTERN_DOC)
    expect(result.current.patternDocState.status).toBe("loading")
    expect(result.current.patternDocState.documentation).toBeNull()
    expect(result.current.patternChatSessionId).toMatch(/^session:\/\//)
  })
})
