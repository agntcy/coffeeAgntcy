/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import {
  CUSTOM_NODE_WIDTH,
  TRANSPORT_NODE_HEIGHT_COMPACT,
  customNodeCardCenterX,
  customNodeCardCenterY,
  transportCenterX,
} from "./graphNodeDimensions"

const BAR_TOP_HANDLES = ["top_left", "top_center", "top_right"] as const
const BAR_BOTTOM_HANDLES = [
  "bottom_left",
  "bottom_center",
  "bottom_right",
] as const

function barHandleForSortedIndex(
  index: number,
  count: number,
  handles: readonly string[],
): string {
  if (count <= 1) return handles[1] ?? handles[0]
  if (count === 2) return index === 0 ? handles[0] : handles[handles.length - 1]
  const slot = Math.round((index / (count - 1)) * (handles.length - 1))
  return handles[slot]
}

export function optimizeBarTransportEdgeHandles(
  nodes: Node[],
  edges: Edge[],
  transportId: string,
): Edge[] {
  const transport = nodes.find((node) => node.id === transportId)
  if (!transport) return edges

  const nodeById = new Map(nodes.map((node) => [node.id, node]))
  const transportY = transport.position.y

  const incomingAbove = edges
    .filter((edge) => edge.target === transportId)
    .filter((edge) => {
      const source = nodeById.get(edge.source)
      return source && source.position.y < transportY
    })
    .sort(
      (a, b) =>
        customNodeCardCenterX(nodeById.get(a.source)!.position) -
        customNodeCardCenterX(nodeById.get(b.source)!.position),
    )

  const outgoingBelow = edges
    .filter((edge) => edge.source === transportId)
    .filter((edge) => {
      const target = nodeById.get(edge.target)
      return target && target.position.y > transportY
    })
    .sort(
      (a, b) =>
        customNodeCardCenterX(nodeById.get(a.target)!.position) -
        customNodeCardCenterX(nodeById.get(b.target)!.position),
    )

  const targetHandleByEdgeId = new Map<string, string>()
  incomingAbove.forEach((edge, index) => {
    targetHandleByEdgeId.set(
      edge.id,
      barHandleForSortedIndex(index, incomingAbove.length, BAR_TOP_HANDLES),
    )
  })

  const sourceHandleByEdgeId = new Map<string, string>()
  outgoingBelow.forEach((edge, index) => {
    sourceHandleByEdgeId.set(
      edge.id,
      barHandleForSortedIndex(index, outgoingBelow.length, BAR_BOTTOM_HANDLES),
    )
  })

  return edges.map((edge) => {
    const targetHandle = targetHandleByEdgeId.get(edge.id)
    const sourceHandle = sourceHandleByEdgeId.get(edge.id)
    if (!targetHandle && !sourceHandle) return edge
    return {
      ...edge,
      ...(targetHandle ? { targetHandle } : {}),
      ...(sourceHandle ? { sourceHandle } : {}),
    }
  })
}

function compactSideHandleForPeer(
  peerCenterX: number,
  centerX: number,
  side: "top" | "bottom",
): string {
  const delta = peerCenterX - centerX
  const threshold = CUSTOM_NODE_WIDTH / 2
  if (delta < -threshold) {
    return side === "top" ? "top_left" : "bottom_left"
  }
  if (delta > threshold) {
    return side === "top" ? "top_right" : "bottom_right"
  }
  return side === "top" ? "top" : "bottom_center"
}

export function optimizeCompactTransportEdgeHandles(
  nodes: Node[],
  edges: Edge[],
  transportId: string,
): Edge[] {
  const transport = nodes.find((node) => node.id === transportId)
  if (!transport) return edges

  const nodeById = new Map(nodes.map((node) => [node.id, node]))
  const centerX = transportCenterX(transport)
  const centerY = transport.position.y + TRANSPORT_NODE_HEIGHT_COMPACT / 2

  return edges.map((edge) => {
    if (edge.target === transportId) {
      const source = nodeById.get(edge.source)
      if (!source) return edge
      const peerCenterX = customNodeCardCenterX(source.position)
      const peerCenterY = customNodeCardCenterY(source.position)
      const side = peerCenterY < centerY ? "top" : "bottom"
      return {
        ...edge,
        targetHandle: compactSideHandleForPeer(peerCenterX, centerX, side),
      }
    }

    if (edge.source === transportId) {
      const target = nodeById.get(edge.target)
      if (!target) return edge
      const peerCenterX = customNodeCardCenterX(target.position)
      const peerCenterY = customNodeCardCenterY(target.position)
      const side = peerCenterY < centerY ? "top" : "bottom"
      return {
        ...edge,
        sourceHandle: compactSideHandleForPeer(peerCenterX, centerX, side),
      }
    }

    return edge
  })
}
