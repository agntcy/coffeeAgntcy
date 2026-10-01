/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it, vi } from "vitest"
import { HttpError } from "@/api/http"
import {
  WORKFLOW_INSTANCE_STATE_MAX_RETRIES,
  WORKFLOW_INSTANTIATE_MAX_RETRIES,
} from "@/config/requestRetryPolicy"

const instantiateWorkflow = vi.fn()
const getWorkflowInstanceState = vi.fn()

vi.mock("@/api/agenticWorkflowsClient", () => ({
  instantiateWorkflow: (...args: unknown[]) => instantiateWorkflow(...args),
  getWorkflowInstanceState: (...args: unknown[]) =>
    getWorkflowInstanceState(...args),
}))

// Retry backoff is irrelevant to the decisions under test. Zero the delays
// rather than stubbing `sleepMs`: the loop now sits in the same module as the
// sleep it calls, so mocking the export no longer intercepts it.
vi.mock("@/config/requestRetryPolicy", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/config/requestRetryPolicy")>()
  return {
    ...actual,
    WORKFLOW_INSTANTIATE_RETRY_DELAYS_MS: [0, 0],
    WORKFLOW_INSTANCE_STATE_RETRY_DELAYS_MS: [0, 0],
  }
})

const { getWorkflowInstanceTopologyWithRetry, instantiateWorkflowWithRetry } =
  await import("./workflowGraphBootstrapRequests")

const BASE_URL = "https://api.test"
const WORKFLOW = "Supervisor"
const PATH_UUID = "550e8400-e29b-41d4-a716-446655440003"

const httpError = (status: number | undefined): HttpError =>
  new HttpError(`failed with ${status}`, { status })

const networkError = (): HttpError =>
  new HttpError("Network error. Please check your connection.")

beforeEach(() => {
  vi.clearAllMocks()
})

describe("instantiateWorkflowWithRetry", () => {
  it("returns the instance id without retrying when the first call succeeds", async () => {
    instantiateWorkflow.mockResolvedValue({
      workflow_instance_id: "instance://abc",
    })

    await expect(
      instantiateWorkflowWithRetry(BASE_URL, WORKFLOW),
    ).resolves.toEqual({ workflow_instance_id: "instance://abc" })
    expect(instantiateWorkflow).toHaveBeenCalledTimes(1)
  })

  it("retries a cold-start network failure and succeeds on a later attempt", async () => {
    instantiateWorkflow
      .mockRejectedValueOnce(networkError())
      .mockResolvedValue({ workflow_instance_id: "instance://abc" })

    await expect(
      instantiateWorkflowWithRetry(BASE_URL, WORKFLOW),
    ).resolves.toEqual({ workflow_instance_id: "instance://abc" })
    expect(instantiateWorkflow).toHaveBeenCalledTimes(2)
  })

  it("stops after the configured budget", async () => {
    instantiateWorkflow.mockRejectedValue(httpError(503))

    await expect(
      instantiateWorkflowWithRetry(BASE_URL, WORKFLOW),
    ).rejects.toBeInstanceOf(HttpError)
    expect(instantiateWorkflow).toHaveBeenCalledTimes(
      WORKFLOW_INSTANTIATE_MAX_RETRIES + 1,
    )
  })

  it.each([
    {
      caseName: "504 merge timeout (the seed event is already queued)",
      status: 504,
    },
    { caseName: "500 catalog inconsistency", status: 500 },
    { caseName: "404 unknown workflow", status: 404 },
    { caseName: "400 schema validation", status: 400 },
  ])(
    "does not replay a non-idempotent POST on $caseName",
    async ({ status }) => {
      instantiateWorkflow.mockRejectedValue(httpError(status))

      await expect(
        instantiateWorkflowWithRetry(BASE_URL, WORKFLOW),
      ).rejects.toBeInstanceOf(HttpError)
      expect(instantiateWorkflow).toHaveBeenCalledTimes(1)
    },
  )

  it("stops retrying once the caller aborts", async () => {
    const controller = new AbortController()
    instantiateWorkflow.mockImplementation(() => {
      controller.abort()
      return Promise.reject(networkError())
    })

    await expect(
      instantiateWorkflowWithRetry(BASE_URL, WORKFLOW, controller.signal),
    ).rejects.toBeInstanceOf(HttpError)
    expect(instantiateWorkflow).toHaveBeenCalledTimes(1)
  })
})

describe("getWorkflowInstanceTopologyWithRetry", () => {
  it("retries server-side failures because the GET is idempotent", async () => {
    getWorkflowInstanceState
      .mockRejectedValueOnce(httpError(504))
      .mockResolvedValue({ topology: { nodes: [] } })

    await expect(
      getWorkflowInstanceTopologyWithRetry(BASE_URL, WORKFLOW, PATH_UUID),
    ).resolves.toEqual({ topology: { nodes: [] } })
    expect(getWorkflowInstanceState).toHaveBeenCalledTimes(2)
  })

  it("never re-runs instantiate when only the topology read fails", async () => {
    getWorkflowInstanceState.mockRejectedValue(httpError(503))

    await expect(
      getWorkflowInstanceTopologyWithRetry(BASE_URL, WORKFLOW, PATH_UUID),
    ).rejects.toBeInstanceOf(HttpError)
    expect(getWorkflowInstanceState).toHaveBeenCalledTimes(
      WORKFLOW_INSTANCE_STATE_MAX_RETRIES + 1,
    )
    expect(instantiateWorkflow).not.toHaveBeenCalled()
  })

  it("surfaces a 404 immediately", async () => {
    getWorkflowInstanceState.mockRejectedValue(httpError(404))

    await expect(
      getWorkflowInstanceTopologyWithRetry(BASE_URL, WORKFLOW, PATH_UUID),
    ).rejects.toBeInstanceOf(HttpError)
    expect(getWorkflowInstanceState).toHaveBeenCalledTimes(1)
  })

  it("requests the topology-only projection", async () => {
    getWorkflowInstanceState.mockResolvedValue({ topology: { nodes: [] } })
    const signal = new AbortController().signal

    await getWorkflowInstanceTopologyWithRetry(
      BASE_URL,
      WORKFLOW,
      PATH_UUID,
      signal,
    )

    expect(getWorkflowInstanceState).toHaveBeenCalledWith(
      BASE_URL,
      WORKFLOW,
      PATH_UUID,
      true,
      signal,
    )
  })
})
