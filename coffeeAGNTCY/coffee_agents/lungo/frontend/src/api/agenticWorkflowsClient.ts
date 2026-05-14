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

export function createClient(baseURL: string): AxiosInstance {
  return axios.create({
    baseURL: baseURL.replace(/\/$/, ""),
    timeout: 60_000,
    headers: { Accept: "application/json" },
  })
}

export function encodeWorkflowPathSegment(workflowName: string): string {
  return encodeURIComponent(workflowName)
}

export function buildWorkflowInstanceSseUrl(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
): string {
  const enc = encodeWorkflowPathSegment(workflowName)
  return `${baseUrl.replace(/\/$/, "")}/agentic-workflows/${enc}/instances/${instancePathUuid}/events/stream`
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
  const path = encodeWorkflowPathSegment(workflowName)
  const { data } = await client.post<InstantiateWorkflowResponseWire>(
    `/agentic-workflows/${path}/`,
  )
  const raw = (data as { workflow_instance_id?: unknown }).workflow_instance_id
  if (raw == null) {
    throw new Error("Missing workflow_instance_id in instantiate response")
  }
  return {
    workflow_instance_id: normalizeInstanceId(raw),
  }
}

export async function getWorkflowInstanceState(
  client: AxiosInstance,
  workflowName: string,
  instancePathUuid: string,
  topologyOnly: boolean,
): Promise<WorkflowInstanceWire> {
  const path = encodeWorkflowPathSegment(workflowName)
  const { data } = await client.get<WorkflowInstanceWire>(
    `/agentic-workflows/${path}/instances/${instancePathUuid}/`,
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
  const normalized = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n")
  const frames: string[] = []
  let rest = normalized
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
        headers: { Accept: "text/event-stream" },
        cache: "no-store",
        signal: controller.signal,
      })
      if (!res.ok || !res.body) {
        onError?.(new Error(`SSE HTTP ${res.status}`))
        return
      }
      // #region agent log
      fetch(
        "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d269ae",
          },
          body: JSON.stringify({
            sessionId: "d269ae",
            location: "agenticWorkflowsClient.ts:subscribeWorkflowInstanceSse",
            message: "sse_http_ok",
            data: { status: res.status },
            timestamp: Date.now(),
            hypothesisId: "H1",
          }),
        },
      ).catch(() => {})
      // #endregion
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let dbgSseFrameBatch = 0
      let dbgChunkLog = 0
      const dispatchFrames = (frames: string[]) => {
        for (const frame of frames) {
          const events = parseSseFrameLines(frame)
          if (events.length > 0 && dbgSseFrameBatch < 25) {
            dbgSseFrameBatch++
            // #region agent log
            fetch(
              "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-Debug-Session-Id": "d269ae",
                },
                body: JSON.stringify({
                  sessionId: "d269ae",
                  location: "agenticWorkflowsClient.ts:sse_read_loop",
                  message: "sse_frame_events",
                  data: {
                    eventsInFrame: events.length,
                    batchIdx: dbgSseFrameBatch,
                    frameLineCount: frame.split("\n").length,
                  },
                  timestamp: Date.now(),
                  hypothesisId: "H1",
                }),
              },
            ).catch(() => {})
            // #endregion
          }
          for (const ev of events) onEvent(ev)
        }
      }
      while (!aborted) {
        const { value, done } = await reader.read()
        // #region agent log
        if (dbgChunkLog < 12 && (value?.byteLength || done)) {
          fetch(
            "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Debug-Session-Id": "d269ae",
              },
              body: JSON.stringify({
                sessionId: "d269ae",
                location: "agenticWorkflowsClient.ts:sse_read_loop",
                message: "sse_read_chunk",
                data: {
                  byteLen: value?.byteLength ?? 0,
                  done,
                  aborted,
                },
                timestamp: Date.now(),
                hypothesisId: "H1b",
              }),
            },
          ).catch(() => {})
          dbgChunkLog++
        }
        // #endregion
        if (value?.byteLength) {
          buffer += decoder.decode(value, { stream: true })
        }
        const split = splitSseFrames(buffer)
        buffer = split.remainder
        dispatchFrames(split.frames)
        if (done) {
          buffer += decoder.decode()
          const tail = splitSseFrames(buffer)
          buffer = tail.remainder
          dispatchFrames(tail.frames)
          break
        }
      }
    } catch (e) {
      if (aborted || controller.signal.aborted) return
      // #region agent log
      fetch(
        "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d269ae",
          },
          body: JSON.stringify({
            sessionId: "d269ae",
            location: "agenticWorkflowsClient.ts:subscribeWorkflowInstanceSse",
            message: "sse_reader_error",
            data: {
              name: e instanceof Error ? e.name : "unknown",
              msg:
                e instanceof Error
                  ? e.message.slice(0, 200)
                  : String(e).slice(0, 200),
              isAbort: e instanceof Error && e.name === "AbortError",
            },
            timestamp: Date.now(),
            hypothesisId: "H1",
          }),
        },
      ).catch(() => {})
      // #endregion
      if (!aborted) onError?.(e)
    }
  }

  void run()

  return () => {
    aborted = true
    controller.abort()
  }
}
