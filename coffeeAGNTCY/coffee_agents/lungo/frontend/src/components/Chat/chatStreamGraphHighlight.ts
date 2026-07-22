/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Map chat stream authors / sequence steps to React Flow graph element ids.
 *
 * The backend owns the graph, so there are no authored NODE_IDS/EDGE_IDS to map
 * from. Stream authors resolve through recruiter/directory slug aliases, inline
 * discovered-agent record keys (CID / record name / label), then live labels.
 * The streaming animation sequence is derived from the live graph topology.
 */

import type { Edge, Node } from "@xyflow/react"
import type { GraphConfig } from "@/utils/graphConfigs"
import { customNodeDataFromNode } from "@/components/MainArea/Graph/Elements/customNodeData"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import { NODE_TYPES } from "@/utils/const"
import {
  getOasfSlugFromNodeData,
  isDirectoryLabel,
} from "@/utils/agenticTopologyIdentityUiMap"
import { buildSenderToNodeMap } from "./groupCommunicationFeedMapping"

function normalizeAuthor(value: string): string {
  return value.trim().toLowerCase()
}

function discoveredAgentLookupKeys(
  data: CustomNodeData | undefined,
): readonly string[] {
  if (!data) return []
  const keys: string[] = []
  if (typeof data.agentCid === "string" && data.agentCid.trim()) {
    keys.push(normalizeAuthor(data.agentCid))
  }
  const record = data.oasfRecord
  if (record && typeof record === "object") {
    const name = record.name
    if (typeof name === "string" && name.trim()) {
      keys.push(normalizeAuthor(name))
    }
  }
  if (typeof data.label === "string" && data.label.trim()) {
    keys.push(normalizeAuthor(data.label))
  }
  return keys
}

function discoveredAgentNodeIdMap(
  graphConfig: GraphConfig | undefined,
): Map<string, string> {
  const map = new Map<string, string>()
  for (const node of graphConfig?.nodes ?? []) {
    const data = customNodeDataFromNode(node)
    if (!data?.oasfRecord && !data?.agentCid) continue
    for (const key of discoveredAgentLookupKeys(data)) {
      if (!map.has(key)) map.set(key, node.id)
    }
  }
  return map
}

/** Known recruiter / directory stream authors mapped to a canonical node slug. */
const AUTHOR_SLUG_ALIASES: Readonly<Record<string, string>> = {
  recruiter_service: "recruiter",
  recruiter_supervisor: "recruiter",
  recruiteragent: "recruiter",
  "agentic recruiter": "recruiter",
  "agntcy agent directory": "directory",
  directory: "directory",
}

/**
 * Stable identity key shared by static-config and API-driven nodes. Transport
 * resolves by type; directory has no OASF slug, so it is detected from its
 * labels; everything else defers to `getOasfSlugFromNodeData`.
 */
function nodeSlugKey(node: Node): string | null {
  if (node.type === NODE_TYPES.TRANSPORT) return "transport"

  const data = customNodeDataFromNode(node)
  const label = data?.label?.toLowerCase() ?? ""
  const label_subtitle = data?.label_subtitle?.toLowerCase() ?? ""
  const combined = `${label} ${label_subtitle}`.trim()
  if (label === "directory" || isDirectoryLabel(combined)) {
    return "directory"
  }

  try {
    return getOasfSlugFromNodeData(data)
  } catch {
    return null
  }
}

function slugToNodeIdMap(
  graphConfig: GraphConfig | undefined,
): Map<string, string> {
  const map = new Map<string, string>()
  for (const node of graphConfig?.nodes ?? []) {
    const slug = nodeSlugKey(node)
    if (slug && !map.has(slug)) map.set(slug, node.id)
  }
  return map
}

/**
 * Resolve a stream event author to a graph node id using recruiter/directory
 * slug aliases first, then live graph labels.
 */
export function resolveStreamAuthorToNodeId(
  author: string | undefined,
  graphConfig?: GraphConfig,
): string | null {
  if (!author?.trim()) return null

  const normalized = normalizeAuthor(author)
  const slug = AUTHOR_SLUG_ALIASES[normalized]
  if (slug) {
    const bySlug = slugToNodeIdMap(graphConfig).get(slug)
    if (bySlug) return bySlug
  }

  const byDiscovered = discoveredAgentNodeIdMap(graphConfig).get(normalized)
  if (byDiscovered) return byDiscovered

  const labelMap = buildSenderToNodeMap(graphConfig)
  return labelMap[author] ?? labelMap[normalized] ?? null
}

/** Highlight ids for the Nth auction stream chunk (0-based). */
export function animationSequenceStepIds(
  graphConfig: GraphConfig | undefined,
  stepIndex: number,
): readonly string[] {
  const step = graphConfig?.animationSequence?.[stepIndex]
  return step?.ids ?? []
}

/**
 * Build a streaming animation sequence straight from the live graph: pulse the
 * root node(s) (no inbound edges, at least one outbound), then the edges fanning
 * out, then the next layer of nodes, and so on. Isolated nodes (e.g. the group
 * container) are skipped. No authored sequence or static config required.
 *
 * Re-entrant edges (fan-in / back-to-source, e.g. a farm replying to the
 * transport) still pulse so no edge that the static sequence animated goes
 * missing; each node is only scheduled once so the traversal still terminates.
 */
export function deriveAnimationSequenceFromGraph(
  nodes: Node[],
  edges: Edge[],
): GraphConfig["animationSequence"] {
  const outgoing = new Map<string, Edge[]>()
  const inDegree = new Map<string, number>()
  for (const node of nodes) inDegree.set(node.id, 0)
  for (const edge of edges) {
    const list = outgoing.get(edge.source) ?? []
    list.push(edge)
    outgoing.set(edge.source, list)
    inDegree.set(edge.target, (inDegree.get(edge.target) ?? 0) + 1)
  }

  const roots = nodes
    .filter(
      (node) => (inDegree.get(node.id) ?? 0) === 0 && outgoing.has(node.id),
    )
    .map((node) => node.id)
  if (roots.length === 0) return []

  const steps: { ids: string[] }[] = [{ ids: [...roots] }]
  const visited = new Set<string>(roots)
  const pulsedEdges = new Set<string>()
  let frontier = roots

  while (frontier.length > 0) {
    const edgeIds: string[] = []
    const nextNodes: string[] = []
    for (const nodeId of frontier) {
      for (const edge of outgoing.get(nodeId) ?? []) {
        if (pulsedEdges.has(edge.id)) continue
        pulsedEdges.add(edge.id)
        edgeIds.push(edge.id)
        if (!visited.has(edge.target) && !nextNodes.includes(edge.target)) {
          nextNodes.push(edge.target)
        }
      }
    }
    for (const id of nextNodes) visited.add(id)
    if (edgeIds.length > 0) steps.push({ ids: edgeIds })
    if (nextNodes.length === 0) break
    steps.push({ ids: nextNodes })
    frontier = nextNodes
  }

  return steps
}
