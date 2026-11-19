/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { renderHook, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { useAppPatternCategoryDoc } from "./useAppPatternCategoryDoc"

vi.mock("@/utils/agenticWorkflowsApi", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/utils/agenticWorkflowsApi")>()
  return {
    ...actual,
    fetchPatternCategoryDocumentation: vi.fn(() => new Promise(() => {})),
  }
})

vi.mock("@/errors/request", () => ({
  reportRequestError: vi.fn(),
}))

describe("useAppPatternCategoryDoc", () => {
  it("shows loading as soon as a category is selected", async () => {
    const initialProps: { category: string | null } = { category: null }
    const { result, rerender } = renderHook(
      ({ category }) => useAppPatternCategoryDoc(category),
      { initialProps },
    )

    expect(result.current.categoryDocState.status).toBe("idle")

    rerender({ category: "supply-chain" })

    await waitFor(() => {
      expect(result.current.categoryDocState.status).toBe("loading")
    })
    expect(result.current.categoryDocState.documentation).toBeNull()
  })
})
