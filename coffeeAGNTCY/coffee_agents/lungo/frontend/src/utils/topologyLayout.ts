/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import { NODE_TYPES } from "@/utils/const"
import {
  CUSTOM_NODE_HEIGHT,
  GROUP_CONTENT_PADDING,
  TRANSPORT_NODE_WIDTH_BAR,
  TRANSPORT_NODE_WIDTH_COMPACT,
} from "./graphNodeDimensions"
import {
  applyPositions,
  bucketNodeLayerY,
  findTransport,
  groupIdsByLayer,
  isCompactTransport,
  placeRowAtCenterX,
  placeRowInContentArea,
  positionsFromNodes,
  rowContentSpan,
  transportCenterX,
  transportHeight,
  type LayoutPoint,
} from "./topologyLayoutGeometry"
import {
  optimizeBarTransportEdgeHandles,
  optimizeCompactTransportEdgeHandles,
} from "./topologyTransportEdges"

export {
  CUSTOM_NODE_HEIGHT,
  CUSTOM_NODE_WIDTH,
  CUSTOM_NODE_X_GAP,
  TRANSPORT_NODE_HEIGHT_COMPACT,
  TRANSPORT_NODE_WIDTH_BAR,
  TRANSPORT_NODE_WIDTH_COMPACT,
} from "./graphNodeDimensions"

export {
  bucketNodeLayerY,
  customNodeCardCenterX,
  customNodeCardCenterY,
} from "./topologyLayoutGeometry"

export {
  optimizeBarTransportEdgeHandles,
  optimizeCompactTransportEdgeHandles,
} from "./topologyTransportEdges"

const Y_GAP = 200
const X_GAP = 280
const ORIGIN_X = 400
const ORIGIN_Y = 60

export function layoutPositionsByLayer(
  nodeIds: string[],
  layerById: Map<string, number>,
): Map<string, LayoutPoint> {
  const byLayer = groupIdsByLayer(nodeIds, (id) => layerById.get(id) ?? 0)
  const layers = [...byLayer.keys()].sort((a, b) => a - b)
  const out = new Map<string, LayoutPoint>()
  for (const layer of layers) {
    const ids = byLayer.get(layer)!
    const y = ORIGIN_Y + layer * Y_GAP
    const totalWidth = (ids.length - 1) * X_GAP
    const x0 = ORIGIN_X - totalWidth / 2
    ids.forEach((id, i) => {
      out.set(id, { x: x0 + i * X_GAP, y })
    })
  }
  return out
}

function layoutBarGraph(nodes: Node[], transport: Node): Node[] {
  const positions = positionsFromNodes(nodes)
  const customIds = nodes
    .filter((node) => node.type !== NODE_TYPES.TRANSPORT)
    .map((node) => node.id)
  const byLayer = groupIdsByLayer(customIds, (id) =>
    bucketNodeLayerY(positions.get(id)!.y),
  )
  for (const ids of byLayer.values()) {
    placeRowAtCenterX(ids, positions, transportCenterX(transport))
  }
  return applyPositions(nodes, positions)
}

/** Centers each custom-node row on the bar transport. Exported for unit tests. */
export function centerCustomNodesOnTransport(
  positions: Map<string, LayoutPoint>,
  layerById: Map<string, number>,
  transportId: string,
  options: { transportCompact?: boolean } = {},
): void {
  if (options.transportCompact) return

  const transportPos = positions.get(transportId)
  if (!transportPos) return

  const centerX = transportPos.x + TRANSPORT_NODE_WIDTH_BAR / 2
  const customIds = [...layerById.keys()].filter((id) => id !== transportId)
  const byLayer = groupIdsByLayer(customIds, (id) => layerById.get(id)!)
  for (const ids of byLayer.values()) {
    placeRowAtCenterX(ids, positions, centerX)
  }
}

function layoutCompactGroup(nodes: Node[], transport: Node): Node[] {
  const group = nodes.find((node) => node.type === NODE_TYPES.GROUP)
  if (!group || transport.parentId !== group.id) return nodes

  const customChildren = nodes.filter(
    (node) =>
      node.parentId === group.id &&
      node.type === NODE_TYPES.CUSTOM &&
      node.id !== transport.id,
  )
  if (customChildren.length === 0) return nodes

  const positions = positionsFromNodes(nodes)
  const customIds = customChildren.map((node) => node.id)
  const byLayer = groupIdsByLayer(customIds, (id) =>
    bucketNodeLayerY(positions.get(id)!.y),
  )

  let contentWidth = TRANSPORT_NODE_WIDTH_COMPACT
  for (const ids of byLayer.values()) {
    contentWidth = Math.max(contentWidth, rowContentSpan(ids.length))
  }
  const groupWidth = contentWidth + GROUP_CONTENT_PADDING * 2

  for (const ids of byLayer.values()) {
    placeRowInContentArea(ids, positions, contentWidth, GROUP_CONTENT_PADDING)
  }

  const transportPos = positions.get(transport.id)!
  positions.set(transport.id, {
    x:
      GROUP_CONTENT_PADDING + (contentWidth - TRANSPORT_NODE_WIDTH_COMPACT) / 2,
    y: transportPos.y,
  })

  const childIds = [transport.id, ...customIds]
  let minY = Infinity
  let maxY = -Infinity
  for (const id of childIds) {
    const pos = positions.get(id)!
    const height =
      id === transport.id ? transportHeight(transport) : CUSTOM_NODE_HEIGHT
    minY = Math.min(minY, pos.y)
    maxY = Math.max(maxY, pos.y + height)
  }
  const shiftY = GROUP_CONTENT_PADDING - minY
  const groupHeight = maxY - minY + GROUP_CONTENT_PADDING * 2

  for (const id of childIds) {
    const pos = positions.get(id)!
    positions.set(id, { x: pos.x, y: pos.y + shiftY })
  }

  return nodes.map((node) => {
    if (node.id === group.id) {
      // The group is hidden, so extent clamping resolves its box from top-level
      // width/height (style is never measured). Write the fitted size there.
      return { ...node, width: groupWidth, height: groupHeight }
    }
    if (node.parentId === group.id) {
      const next = positions.get(node.id)
      return next ? { ...node, position: next } : node
    }
    return node
  })
}

/** Positions nodes and optimizes transport edge handles for SLIM bar or compact graphs. */
export function layoutSlimTransportGraph(
  nodes: Node[],
  edges: Edge[],
): { nodes: Node[]; edges: Edge[] } {
  const transport = findTransport(nodes)
  if (!transport) return { nodes, edges }

  const compact = isCompactTransport(transport)
  const laidOutNodes = compact
    ? layoutCompactGroup(nodes, transport)
    : layoutBarGraph(nodes, transport)
  const laidOutEdges = compact
    ? optimizeCompactTransportEdgeHandles(laidOutNodes, edges, transport.id)
    : optimizeBarTransportEdgeHandles(laidOutNodes, edges, transport.id)

  return { nodes: laidOutNodes, edges: laidOutEdges }
}
