/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { renderHook, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import { fetchWorkflowSummariesWithRetry } from "@/utils/agenticWorkflowsApi"
import { useAppWorkflowCatalog } from "./useAppWorkflowCatalog"

vi.mock("@/utils/agenticWorkflowsApi", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/utils/agenticWorkflowsApi")>()
  return {
    ...actual,
    fetchWorkflowSummariesWithRetry: vi.fn(),
  }
})

vi.mock("@/errors/request", () => ({
  reportRequestError: vi.fn(),
}))

const groupSummary: WorkflowSummary = {
  name: "supply-chain",
  pattern: "group_messaging",
  pattern_category: "supply",
  use_case: "order",
  scenario: "demo",
  supports_sse: true,
  supports_streaming: false,
  chat_api_target: "exchange",
}

describe("useAppWorkflowCatalog", () => {
  it("selects the group-messaging default when the catalog arrives", async () => {
    vi.mocked(fetchWorkflowSummariesWithRetry).mockResolvedValue([groupSummary])

    const { result } = renderHook(() => useAppWorkflowCatalog())

    await waitFor(() => {
      expect(result.current.selectedWorkflowSummary?.name).toBe("supply-chain")
    })
    expect(result.current.workflowCatalogLoading).toBe(false)
    expect(result.current.workflowCatalogError).toBeNull()
  })
})
