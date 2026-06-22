/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * Transport-name patch for the API-driven graph.
 *
 * Mirrors `updateTransportLabels`, but targets dynamically rendered nodes/edges:
 * transport nodes by React Flow type and MCP edges by their "MCP: " label prefix
 * instead of the authored static ids that no longer exist once the backend owns
 * the topology. The transport config is immutable per deployment, so the fetch
 * result is cached and the state patch is idempotent (returns the same array when
 * nothing changes) to stay cheap when called after every topology apply.
 * -----------------------------------------------------------------------------
 */

import type { Edge, Node } from "@xyflow/react"
import { EDGE_LABELS, NODE_TYPES } from "./const"
import { logger } from "./logger"
import { joinBaseUrl, LUNGO_FRONTEND_URLS } from "@/urls"
import { getApiUrlForPattern, supportsTransportUpdates } from "./patternUtils"

// Cache the in-flight (and resolved) fetch promise per url so overlapping
// topology applies share one request; evict on failure/empty so a later apply
// can retry.
const transportNameByUrl = new Map<string, Promise<string | null>>()

export function transportGithubLink(
  transport: string,
  isStreaming: boolean,
): string {
  const transportUrls = isStreaming
    ? LUNGO_FRONTEND_URLS.github.transports.streaming
    : LUNGO_FRONTEND_URLS.github.transports.regular
  if (transport === "SLIM") {
    return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.slim}`
  }
  if (transport === "NATS") {
    return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.nats}`
  }
  return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.general}`
}

async function fetchTransportName(url: string): Promise<string | null> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  const data = await response.json()
  const transport = data.transport
  if (typeof transport !== "string" || transport.length === 0) return null
  return transport
}

function evictOnEmpty(url: string, name: string | null): void {
  if (!name) transportNameByUrl.delete(url)
}

function evictOnError(url: string): void {
  transportNameByUrl.delete(url)
}

function resolveTransportName(url: string): Promise<string | null> {
  const inflight = transportNameByUrl.get(url)
  if (inflight) return inflight
  const pending = fetchTransportName(url)
  transportNameByUrl.set(url, pending)
  pending.then(
    (name) => evictOnEmpty(url, name),
    () => evictOnError(url),
  )
  return pending
}

function patchTransportNodes(
  setNodes: (updater: (nodes: Node[]) => Node[]) => void,
  label: string,
  githubLink: string,
): void {
  setNodes((nodes) => {
    let changed = false
    const next = nodes.map((node) => {
      if (node.type !== NODE_TYPES.TRANSPORT) return node
      const data = node.data as { label?: unknown; githubLink?: unknown }
      if (data.label === label && data.githubLink === githubLink) return node
      changed = true
      return { ...node, data: { ...node.data, label, githubLink } }
    })
    return changed ? next : nodes
  })
}

function patchMcpEdges(
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void,
  mcpLabel: string,
): void {
  setEdges((edges) => {
    let changed = false
    const next = edges.map((edge) => {
      const label = (edge.data as { label?: unknown } | undefined)?.label
      if (typeof label !== "string" || !label.startsWith(EDGE_LABELS.MCP)) {
        return edge
      }
      // MCP_WITH_STDIO also starts with the "MCP: " prefix but is a distinct
      // A2A edge label, not a transport-named MCP edge; leave it untouched.
      if (label === EDGE_LABELS.MCP_WITH_STDIO) return edge
      if (label === mcpLabel) return edge
      changed = true
      return { ...edge, data: { ...edge.data, label: mcpLabel } }
    })
    return changed ? next : edges
  })
}

/**
 * Fetch the live transport name and stamp it onto dynamic transport nodes and
 * MCP edges. No-op for patterns without a transport config endpoint.
 */
export async function applyDynamicTransportLabels(
  setNodes: (updater: (nodes: Node[]) => Node[]) => void,
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void,
  pattern?: string,
  isStreaming?: boolean,
): Promise<void> {
  if (!supportsTransportUpdates(pattern)) return

  const url = joinBaseUrl(
    getApiUrlForPattern(pattern),
    LUNGO_FRONTEND_URLS.apiPaths.transportConfig,
  )

  try {
    const transport = await resolveTransportName(url)
    if (!transport) return
    patchTransportNodes(
      setNodes,
      `Transport: ${transport}`,
      transportGithubLink(transport, Boolean(isStreaming)),
    )
    patchMcpEdges(setEdges, `${EDGE_LABELS.MCP}${transport}`)
  } catch (error) {
    logger.apiError(LUNGO_FRONTEND_URLS.apiPaths.transportConfig, error)
  }
}
