/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import axios, { type AxiosInstance } from "axios"
import type {
  EventV1Wire,
  InstantiateWorkflowResponseWire,
  WorkflowInstanceWire,
} from "@/api/agenticWorkflowsTypes"
import {
  buildWorkflowInstanceSseUrl,
  getAgenticWorkflowsApiKey,
  LUNGO_FRONTEND_URLS,
} from "@/urls"

export function agenticWorkflowsAuthHeaders(): Record<string, string> {
  const key = getAgenticWorkflowsApiKey()
  if (!key) return {}
  return { Authorization: `Bearer ${key}` }
}

export function createClient(baseURL: string): AxiosInstance {
  return axios.create({
    baseURL: baseURL.replace(/\/$/, ""),
    timeout: 60_000,
    headers: {
      Accept: "application/json",
      ...agenticWorkflowsAuthHeaders(),
    },
  })
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
  client: AxiosInstance,
  workflowName: string,
): Promise<InstantiateWorkflowResponseWire> {
  const { data } = await client.post<InstantiateWorkflowResponseWire>(
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstantiate(workflowName),
  )
  const raw = (data as { workflow_instance_id?: unknown }).workflow_instance_id
  if (raw == null) {
    throw new Error("Missing workflow_instance_id in instantiate response")
  }
  return {
    workflow_instance_id: normalizeInstanceId(raw),
  }
}

export async function deleteWorkflowInstance(
  client: AxiosInstance,
  workflowName: string,
  instancePathUuid: string,
): Promise<void> {
  await client.delete(
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstance(
      workflowName,
      instancePathUuid,
    ),
  )
}

export async function getWorkflowInstanceState(
  client: AxiosInstance,
  workflowName: string,
  instancePathUuid: string,
  topologyOnly: boolean,
): Promise<WorkflowInstanceWire> {
  const { data } = await client.get<WorkflowInstanceWire>(
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstance(
      workflowName,
      instancePathUuid,
    ),
    { params: topologyOnly ? { topology_only: true } : undefined },
  )
  return data
}

/** Parse `instance://uuid` into lowercase UUID string for path segments. */
export function instanceIdToPathUuid(instanceId: string): string {
  const prefix = "instance://"
  if (!instanceId.startsWith(prefix)) {
    throw new Error(`Expected instance id to start with ${prefix}`)
  }
  return instanceId.slice(prefix.length)
}

export function parseSseDataLine(line: string): EventV1Wire | null {
  const trimmed = line.trim()
  if (!trimmed.startsWith("data:")) return null
  const jsonPart = trimmed.slice(5).trim()
  if (!jsonPart) return null
  try {
    return JSON.parse(jsonPart) as EventV1Wire
  } catch {
    return null
  }
}

export function splitSseFrames(buffer: string): {
  frames: string[]
  remainder: string
} {
  const frames: string[] = []
  let rest = buffer
  let idx: number
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    frames.push(rest.slice(0, idx))
    rest = rest.slice(idx + 2)
  }
  return { frames, remainder: rest }
}

export function parseSseFrameLines(frame: string): EventV1Wire[] {
  const events: EventV1Wire[] = []
  const lines = frame.split("\n")
  for (const line of lines) {
    if (!line.length || line.startsWith(":")) continue
    const ev = parseSseDataLine(line)
    if (ev) events.push(ev)
  }
  return events
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
  const url = buildWorkflowInstanceSseUrl(
    baseUrl,
    workflowName,
    instancePathUuid,
  )

  let aborted = false
  let buffer = ""
  const controller = new AbortController()

  const run = async () => {
    try {
      const res = await fetch(url, {
        headers: {
          Accept: "text/event-stream",
          ...agenticWorkflowsAuthHeaders(),
        },
        cache: "no-store",
        signal: controller.signal,
      })
      if (!res.ok || !res.body) {
        onError?.(new Error(`SSE HTTP ${res.status}`))
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      while (!aborted) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const { frames, remainder } = splitSseFrames(buffer)
        buffer = remainder
        for (const frame of frames) {
          const events = parseSseFrameLines(frame)
          for (const ev of events) onEvent(ev)
        }
      }
    } catch (e) {
      if (controller.signal.aborted) return
      if (!aborted) onError?.(e)
    }
  }

  void run()

  return () => {
    aborted = true
    controller.abort()
  }
}
