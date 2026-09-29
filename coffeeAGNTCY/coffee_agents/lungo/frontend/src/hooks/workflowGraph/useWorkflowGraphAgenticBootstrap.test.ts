/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import type { RefObject } from "react"
import type { EventV1Wire } from "@/api/agenticWorkflowsTypes"
import type { WorkflowGraphAgenticSession } from "./useWorkflowGraphFromAgenticApi.types"

type OnEvent = (event: EventV1Wire) => void
type OnError = (error: unknown) => void

type Subscription = {
  workflowName: string
  onEvent: OnEvent
  onError: OnError
  close: ReturnType<typeof vi.fn>
}

const subscriptions: Subscription[] = []
const instantiateWorkflowWithRetry = vi.fn()
const getWorkflowInstanceTopologyWithRetry = vi.fn()

vi.mock("@/api/agenticWorkflowsClient", () => ({
  instanceIdToPathUuid: (instanceId: string) =>
    instanceId.slice("instance://".length),
  subscribeWorkflowInstanceSse: (
    _baseUrl: string,
    workflowName: string,
    _pathUuid: string,
    onEvent: OnEvent,
    onError: OnError,
  ) => {
    const close = vi.fn()
    subscriptions.push({ workflowName, onEvent, onError, close })
    return close
  },
}))

vi.mock("./workflowGraphBootstrapRequests", () => ({
  instantiateWorkflowWithRetry: (...args: unknown[]) =>
    instantiateWorkflowWithRetry(...args),
  getWorkflowInstanceTopologyWithRetry: (...args: unknown[]) =>
    getWorkflowInstanceTopologyWithRetry(...args),
}))

vi.mock("@/errors/request", () => ({
  reportRequestError: vi.fn(() => ({ message: "reported" })),
}))

const { useWorkflowGraphAgenticBootstrap } =
  await import("./useWorkflowGraphAgenticBootstrap")

const BASE_URL = "https://api.test"
const FRAME = { id: "event" } as unknown as EventV1Wire

const ref = <T>(current: T): RefObject<T> => ({ current })

/**
 * Mirrors the real owner of the session ref: `clearSession` drops it, and the
 * bootstrap effect assigns a fresh one once it has instantiated the workflow.
 */
function setup(initialWorkflow: string) {
  const sessionRef = ref<WorkflowGraphAgenticSession | null>(null)
  const clearSession = vi.fn(() => {
    sessionRef.current?.closeSse?.()
    sessionRef.current = null
  })
  const setAgenticError = vi.fn()
  const handleSseEvent = vi.fn()

  const hook = renderHook(
    ({ workflow }: { workflow: string }) =>
      useWorkflowGraphAgenticBootstrap({
        agenticMode: true,
        baseUrl: BASE_URL,
        catalogWorkflowName: workflow,
        sessionRef,
        applyInstanceTopologyRef: ref(vi.fn()),
        handleWorkflowInstanceSseEventRef: ref(handleSseEvent),
        clearSessionRef: ref(clearSession),
        setAgenticError,
        setWorkflowInstanceId: vi.fn(),
      }),
    { initialProps: { workflow: initialWorkflow } },
  )

  return { ...hook, sessionRef, setAgenticError, handleSseEvent }
}

const subscriptionFor = (workflowName: string): Subscription => {
  const found = subscriptions.find((s) => s.workflowName === workflowName)
  if (!found) throw new Error(`no SSE subscription for ${workflowName}`)
  return found
}

beforeEach(() => {
  subscriptions.length = 0
  vi.clearAllMocks()
  instantiateWorkflowWithRetry.mockImplementation(
    async (_baseUrl: string, workflowName: string) => ({
      workflow_instance_id: `instance://${workflowName}`,
    }),
  )
  getWorkflowInstanceTopologyWithRetry.mockResolvedValue({ topology: {} })
})

describe("useWorkflowGraphAgenticBootstrap SSE frames", () => {
  it("clears the banner, resets the reconnect budget and forwards a live frame", async () => {
    const { sessionRef, setAgenticError, handleSseEvent } = setup("Alpha")
    await waitFor(() => expect(subscriptions).toHaveLength(1))
    sessionRef.current!.sseReconnectAttempts = 4
    setAgenticError.mockClear()

    subscriptionFor("Alpha").onEvent(FRAME)

    expect(sessionRef.current!.sseReconnectAttempts).toBe(0)
    expect(setAgenticError).toHaveBeenCalledWith(null)
    expect(handleSseEvent).toHaveBeenCalledWith(
      FRAME,
      "Alpha",
      "instance://Alpha",
    )
  })

  it("ignores a frame from a superseded session, keeping the banner and the new session's state", async () => {
    const { rerender, sessionRef, setAgenticError, handleSseEvent } =
      setup("Alpha")
    await waitFor(() => expect(subscriptions).toHaveLength(1))
    const staleOnEvent = subscriptionFor("Alpha").onEvent

    rerender({ workflow: "Beta" })
    await waitFor(() => expect(subscriptions).toHaveLength(2))
    sessionRef.current!.sseReconnectAttempts = 3
    setAgenticError.mockClear()

    staleOnEvent(FRAME)

    expect(setAgenticError).not.toHaveBeenCalled()
    expect(handleSseEvent).not.toHaveBeenCalled()
    expect(sessionRef.current!.instanceId).toBe("instance://Beta")
    expect(sessionRef.current!.sseReconnectAttempts).toBe(3)
  })

  it("ignores a frame that arrives after the session was cleared", async () => {
    const { sessionRef, setAgenticError, handleSseEvent } = setup("Alpha")
    await waitFor(() => expect(subscriptions).toHaveLength(1))
    const { onEvent } = subscriptionFor("Alpha")
    sessionRef.current = null
    setAgenticError.mockClear()

    onEvent(FRAME)

    expect(setAgenticError).not.toHaveBeenCalled()
    expect(handleSseEvent).not.toHaveBeenCalled()
  })

  it("ignores a frame that arrives after unmount", async () => {
    const { unmount, setAgenticError, handleSseEvent } = setup("Alpha")
    await waitFor(() => expect(subscriptions).toHaveLength(1))
    const { onEvent } = subscriptionFor("Alpha")

    unmount()
    setAgenticError.mockClear()
    onEvent(FRAME)

    expect(setAgenticError).not.toHaveBeenCalled()
    expect(handleSseEvent).not.toHaveBeenCalled()
  })

  it("keeps the 'updates stopped' banner when a stale stream delivers a late frame", async () => {
    const { rerender, sessionRef, setAgenticError } = setup("Alpha")
    await waitFor(() => expect(subscriptions).toHaveLength(1))
    const staleOnEvent = subscriptionFor("Alpha").onEvent

    rerender({ workflow: "Beta" })
    await waitFor(() => expect(subscriptions).toHaveLength(2))
    // The live session exhausts its reconnect budget and raises the banner.
    sessionRef.current!.sseReconnectAttempts = 6
    subscriptionFor("Beta").onError(new Error("stream dropped"))
    expect(setAgenticError).toHaveBeenLastCalledWith(
      "Live workflow updates stopped. The graph may be outdated.",
    )

    staleOnEvent(FRAME)

    expect(setAgenticError).toHaveBeenLastCalledWith(
      "Live workflow updates stopped. The graph may be outdated.",
    )
  })
})
