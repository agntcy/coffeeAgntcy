/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook } from "@testing-library/react"
import type { Node } from "@xyflow/react"
import type { TopologyWire } from "@/api/agenticWorkflowsTypes"
import {
  TOPOLOGY_REFETCH_DEBOUNCE_MS,
  TOPOLOGY_REFETCH_RETRY_DELAYS_MS,
} from "@/config/requestRetryPolicy"
import type { WorkflowGraphAgenticSession } from "./useWorkflowGraphFromAgenticApi.types"

const getWorkflowInstanceState = vi.fn()

vi.mock("@/api/agenticWorkflowsClient", () => ({
  getWorkflowInstanceState: (...args: unknown[]) =>
    getWorkflowInstanceState(...args),
  instanceIdToPathUuid: (instanceId: string) =>
    instanceId.slice("instance://".length),
}))

vi.mock("@/errors/request", () => ({ reportRequestError: vi.fn() }))

vi.mock("@/utils/topologyToReactFlow", () => ({
  topologyWireToReactFlow: () => ({ nodes: [{ id: "a" }], edges: [] }),
}))

const { useWorkflowGraphTopologySync } =
  await import("./useWorkflowGraphTopologySync")

const REFRESH_FAILED =
  "Could not refresh the workflow graph. It may be outdated."
const TOPOLOGY = { nodes: [], edges: [] } as unknown as TopologyWire

const session = (): WorkflowGraphAgenticSession => ({
  baseUrl: "https://api.test",
  workflowName: "Alpha",
  instanceId: "instance://alpha",
  pathUuid: "alpha",
  closeSse: null,
  debounceTimer: null,
  retryTimer: null,
  sseReconnectTimer: null,
  refetchSeq: 0,
  sseReconnectAttempts: 0,
})

function setup() {
  const setAgenticError = vi.fn()
  const setNodes = vi.fn()
  const setEdges = vi.fn()
  const onApplied = vi.fn()
  const sessionRef = {
    current: session() as WorkflowGraphAgenticSession | null,
  }

  const { result } = renderHook(() =>
    useWorkflowGraphTopologySync({
      isStreamingRef: { current: false },
      sessionRef,
      onAppliedRef: { current: onApplied },
      attachHandlers: (node: Node) => node,
      setNodes,
      setEdges,
      restoreEdgeAnimation: vi.fn(),
      setAgenticError,
    }),
  )

  return { ...result.current, setAgenticError, setNodes, setEdges, onApplied }
}

beforeEach(() => {
  vi.useFakeTimers()
  getWorkflowInstanceState.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe("useWorkflowGraphTopologySync error banner", () => {
  it("clears the banner when a topology is applied", () => {
    const { applyInstanceTopologyRef, setAgenticError, setNodes, onApplied } =
      setup()

    applyInstanceTopologyRef.current(TOPOLOGY)

    expect(setNodes).toHaveBeenCalledTimes(1)
    expect(onApplied).toHaveBeenCalledWith(["a"])
    expect(setAgenticError).toHaveBeenCalledWith(null)
  })

  it("raises the banner once the refetch budget is spent", async () => {
    getWorkflowInstanceState.mockRejectedValue(new Error("down"))
    const { scheduleTopologyRefetchRef, setAgenticError } = setup()

    scheduleTopologyRefetchRef.current()
    await vi.advanceTimersByTimeAsync(
      TOPOLOGY_REFETCH_DEBOUNCE_MS +
        TOPOLOGY_REFETCH_RETRY_DELAYS_MS[0] +
        TOPOLOGY_REFETCH_RETRY_DELAYS_MS[1],
    )

    expect(getWorkflowInstanceState).toHaveBeenCalledTimes(3)
    expect(setAgenticError).toHaveBeenCalledWith(REFRESH_FAILED)
  })

  it("keeps the banner while refetches fail and clears it only when one succeeds", async () => {
    getWorkflowInstanceState.mockRejectedValue(new Error("down"))
    const { scheduleTopologyRefetchRef, setAgenticError } = setup()

    scheduleTopologyRefetchRef.current()
    await vi.advanceTimersByTimeAsync(1_000)
    expect(setAgenticError).toHaveBeenCalledWith(REFRESH_FAILED)
    setAgenticError.mockClear()

    // Still failing: a retry that fails again must not hide the banner.
    scheduleTopologyRefetchRef.current()
    await vi.advanceTimersByTimeAsync(TOPOLOGY_REFETCH_DEBOUNCE_MS)
    expect(setAgenticError).not.toHaveBeenCalledWith(null)

    // Backend recovers: the next refetch applies a topology and clears it.
    getWorkflowInstanceState.mockResolvedValue({ topology: TOPOLOGY })
    await vi.advanceTimersByTimeAsync(1_000)
    scheduleTopologyRefetchRef.current()
    await vi.advanceTimersByTimeAsync(TOPOLOGY_REFETCH_DEBOUNCE_MS)

    expect(setAgenticError).toHaveBeenCalledWith(null)
  })
})
