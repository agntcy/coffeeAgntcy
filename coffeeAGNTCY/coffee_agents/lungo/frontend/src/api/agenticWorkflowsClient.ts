/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { fetchJson, fetchSse, httpFetch } from "@/api/http"
import type {
  EventV1Wire,
  InstantiateWorkflowResponseWire,
  WorkflowInstanceWire,
} from "@/api/agenticWorkflowsTypes"
import {
  buildAgenticWorkflowsInstantiateRequest,
  buildAgenticWorkflowsInstanceRequest,
  buildAgenticWorkflowsInstanceSseRequest,
  getAgenticWorkflowsApiKey,
} from "@/urls"

export {
  parseSseDataLine,
  parseSseFrameLines,
  splitSseFrames,
} from "@/api/http/sseParsing"

export function agenticWorkflowsAuthHeaders(): Record<string, string> {
  const key = getAgenticWorkflowsApiKey()
  if (!key) return {}
  return { Authorization: `Bearer ${key}` }
}

function normalizeInstanceId(raw: unknown): string {
  if (typeof raw === "string") return raw
  if (
    raw &&
    typeof raw === "object" &&
    "root" in raw &&
    typeof (raw as { root: unknown }).root === "string"
  ) {
    return (raw as { root: string }).root
  }
  return String(raw)
}

export async function instantiateWorkflow(
  baseUrl: string,
  workflowName: string,
): Promise<InstantiateWorkflowResponseWire> {
  const request = buildAgenticWorkflowsInstantiateRequest(workflowName, baseUrl)
  const data = await fetchJson<{ workflow_instance_id?: unknown }>(
    request.url,
    {
      method: "POST",
      endpointLabel: request.endpointLabel,
      headers: agenticWorkflowsAuthHeaders(),
    },
  )
  const raw = data.workflow_instance_id
  if (raw == null) {
    throw new Error("Missing workflow_instance_id in instantiate response")
  }
  return {
    workflow_instance_id: normalizeInstanceId(raw),
  }
}

export async function deleteWorkflowInstance(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
): Promise<void> {
  const request = buildAgenticWorkflowsInstanceRequest(
    workflowName,
    instancePathUuid,
    { baseUrl },
  )
  await httpFetch(request.url, {
    method: "DELETE",
    endpointLabel: request.endpointLabel,
    headers: agenticWorkflowsAuthHeaders(),
  })
}

export async function getWorkflowInstanceState(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
  topologyOnly: boolean,
): Promise<WorkflowInstanceWire> {
  const request = buildAgenticWorkflowsInstanceRequest(
    workflowName,
    instancePathUuid,
    { baseUrl, topologyOnly },
  )

  return fetchJson<WorkflowInstanceWire>(request.url, {
    endpointLabel: request.endpointLabel,
    headers: agenticWorkflowsAuthHeaders(),
  })
}

/** Parse `instance://uuid` into lowercase UUID string for path segments. */
export function instanceIdToPathUuid(instanceId: string): string {
  const prefix = "instance://"
  if (!instanceId.startsWith(prefix)) {
    throw new Error(`Expected instance id to start with ${prefix}`)
  }
  return instanceId.slice(prefix.length)
}

export function eventTouchesInstance(
  event: EventV1Wire,
  workflowName: string,
  instanceId: string,
): boolean {
  const wf = event.data?.workflows?.[workflowName]
  const inst = wf?.instances
  if (!inst || typeof inst !== "object") return false
  return Object.prototype.hasOwnProperty.call(inst, instanceId)
}

export type WorkflowInstanceSseClose = () => void

/**
 * Subscribe to workflow instance SSE. Parses `data:` JSON lines; ignores comment frames (`:`).
 * Calls `onEvent` for each parsed `event_v1` object.
 */
export function subscribeWorkflowInstanceSse(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
  onEvent: (event: EventV1Wire) => void,
  onError?: (err: unknown) => void,
): WorkflowInstanceSseClose {
  const request = buildAgenticWorkflowsInstanceSseRequest(
    workflowName,
    instancePathUuid,
    baseUrl,
  )

  return fetchSse<EventV1Wire>(request.url, {
    endpointLabel: request.endpointLabel,
    headers: agenticWorkflowsAuthHeaders(),
    onEvent,
    onError,
  })
}
