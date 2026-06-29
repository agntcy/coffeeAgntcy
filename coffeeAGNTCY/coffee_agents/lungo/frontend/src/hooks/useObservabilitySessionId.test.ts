/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it, vi, beforeEach } from "vitest"
import { renderHook } from "@testing-library/react"
import { useObservabilitySessionId } from "./useObservabilitySessionId"
import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { useStreamingSessionId } from "@/stores/auctionStreamingStore"
import { useRecruiterStreamingSessionId } from "@/stores/recruiterStreamingStore"

vi.mock("@/stores/groupStreamingStore", () => ({
  useGroupSessionId: vi.fn(),
}))

vi.mock("@/stores/auctionStreamingStore", () => ({
  useStreamingSessionId: vi.fn(),
}))

vi.mock("@/stores/recruiterStreamingStore", () => ({
  useRecruiterStreamingSessionId: vi.fn(),
}))

const mockStores = (
  group: string | null,
  auction: string | null,
  recruiter: string | null,
) => {
  vi.mocked(useGroupSessionId).mockReturnValue(group)
  vi.mocked(useStreamingSessionId).mockReturnValue(auction)
  vi.mocked(useRecruiterStreamingSessionId).mockReturnValue(recruiter)
}

describe("useObservabilitySessionId", () => {
  beforeEach(() => {
    mockStores("group-sid", "auction-sid", "recruiter-sid")
  })

  it("prefers agentResponse session id over store values", () => {
    const { result } = renderHook(() => useObservabilitySessionId("api-sid"))
    expect(result.current).toBe("api-sid")
  })

  it("falls back to group session id", () => {
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("group-sid")
  })

  it("falls back to auction session id when group is empty", () => {
    mockStores(null, "auction-sid", "recruiter-sid")
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("auction-sid")
  })

  it("falls back to recruiter session id when earlier sources are empty", () => {
    mockStores(null, null, "recruiter-sid")
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("recruiter-sid")
  })

  it("returns null when no session id is available", () => {
    mockStores(null, null, null)
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBeNull()
  })
})
