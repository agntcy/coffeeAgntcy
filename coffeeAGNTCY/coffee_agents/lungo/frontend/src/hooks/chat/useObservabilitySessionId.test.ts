/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it, vi, beforeEach } from "vitest"
import { renderHook } from "@testing-library/react"
import { useObservabilitySessionId } from "./useObservabilitySessionId"
import { useGroupSessionId } from "@/stores/groupStreamingStore"
import { useStreamingSessionId } from "@/stores/auctionStreamingStore"
import {
  useRecruiterStreamingSessionId,
  useRecruiterTraceId,
} from "@/stores/recruiterStreamingStore"

vi.mock("@/stores/groupStreamingStore", () => ({
  useGroupSessionId: vi.fn(),
}))

vi.mock("@/stores/auctionStreamingStore", () => ({
  useStreamingSessionId: vi.fn(),
}))

vi.mock("@/stores/recruiterStreamingStore", () => ({
  useRecruiterStreamingSessionId: vi.fn(),
  useRecruiterTraceId: vi.fn(),
}))

const mockStores = (
  group: string | null,
  auction: string | null,
  recruiterSession: string | null,
  recruiterTrace: string | null = null,
) => {
  vi.mocked(useGroupSessionId).mockReturnValue(group)
  vi.mocked(useStreamingSessionId).mockReturnValue(auction)
  vi.mocked(useRecruiterStreamingSessionId).mockReturnValue(recruiterSession)
  vi.mocked(useRecruiterTraceId).mockReturnValue(recruiterTrace)
}

describe("useObservabilitySessionId", () => {
  beforeEach(() => {
    mockStores(
      "group-sid",
      "auction-sid",
      "recruiter-adk-sid",
      "recruiter-trace-id",
    )
  })

  it("prefers agentResponse trace id over all store values", () => {
    const { result } = renderHook(() =>
      useObservabilitySessionId("api-adk-sid", "api-trace-id"),
    )
    expect(result.current).toBe("api-trace-id")
  })

  it("prefers agentResponse trace id over agentResponse session id", () => {
    mockStores(null, null, null, null)
    const { result } = renderHook(() =>
      useObservabilitySessionId("adk-sid", "execution-trace"),
    )
    expect(result.current).toBe("execution-trace")
  })

  it("prefers recruiter trace id over group and auction session ids", () => {
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("recruiter-trace-id")
  })

  it("falls back to group session id when no trace ids are available", () => {
    mockStores("group-sid", "auction-sid", "recruiter-adk-sid", null)
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("group-sid")
  })

  it("falls back to auction session id when group and trace ids are empty", () => {
    mockStores(null, "auction-sid", "recruiter-adk-sid", null)
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("auction-sid")
  })

  it("uses agentResponse session id as legacy fallback for batch patterns", () => {
    mockStores(null, null, null, null)
    const { result } = renderHook(() =>
      useObservabilitySessionId("api-legacy-trace-sid"),
    )
    expect(result.current).toBe("api-legacy-trace-sid")
  })

  it("falls back to recruiter ADK session id only when no trace id exists", () => {
    mockStores(null, null, "recruiter-adk-sid", null)
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBe("recruiter-adk-sid")
  })

  it("returns null when no observability id is available", () => {
    mockStores(null, null, null, null)
    const { result } = renderHook(() => useObservabilitySessionId(undefined))
    expect(result.current).toBeNull()
  })
})
