/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Node } from "@xyflow/react"
import { NODE_TYPES } from "@/utils/const"
import {
  CUSTOM_NODE_WIDTH,
  CUSTOM_NODE_X_GAP,
  LAYER_Y_BUCKET,
  TRANSPORT_NODE_HEIGHT_BAR,
  TRANSPORT_NODE_HEIGHT_COMPACT,
  TRANSPORT_NODE_WIDTH_BAR,
  TRANSPORT_NODE_WIDTH_COMPACT,
  customNodeCardCenterX,
  customNodeCardCenterY,
  transportCenterX,
} from "./graphNodeDimensions"

export { customNodeCardCenterX, customNodeCardCenterY, transportCenterX }

export type LayoutPoint = { x: number; y: number }

export function bucketNodeLayerY(y: number): number {
  return Math.round(y / LAYER_Y_BUCKET) * LAYER_Y_BUCKET
}

export function rowContentSpan(nodeCount: number): number {
  return (nodeCount - 1) * CUSTOM_NODE_X_GAP + CUSTOM_NODE_WIDTH
}

export function sortedRowIds(
  ids: string[],
  positions: Map<string, LayoutPoint>,
): string[] {
  return [...ids].sort((a, b) => positions.get(a)!.x - positions.get(b)!.x)
}

export function placeRowAtCenterX(
  ids: string[],
  positions: Map<string, LayoutPoint>,
  centerX: number,
): void {
  const sorted = sortedRowIds(ids, positions)
  const firstLeft =
    centerX -
    CUSTOM_NODE_WIDTH / 2 -
    ((sorted.length - 1) / 2) * CUSTOM_NODE_X_GAP
  sorted.forEach((id, index) => {
    const point = positions.get(id)!
    positions.set(id, {
      x: firstLeft + index * CUSTOM_NODE_X_GAP,
      y: point.y,
    })
  })
}

export function placeRowInContentArea(
  ids: string[],
  positions: Map<string, LayoutPoint>,
  contentWidth: number,
  padding: number,
): void {
  const sorted = sortedRowIds(ids, positions)
  const layerLeft = padding + (contentWidth - rowContentSpan(sorted.length)) / 2
  sorted.forEach((id, index) => {
    const point = positions.get(id)!
    positions.set(id, {
      x: layerLeft + index * CUSTOM_NODE_X_GAP,
      y: point.y,
    })
  })
}

export function groupIdsByLayer(
  ids: string[],
  layerOf: (id: string) => number,
): Map<number, string[]> {
  const byLayer = new Map<number, string[]>()
  for (const id of ids) {
    const layer = layerOf(id)
    if (!byLayer.has(layer)) byLayer.set(layer, [])
    byLayer.get(layer)!.push(id)
  }
  return byLayer
}

export function positionsFromNodes(nodes: Node[]): Map<string, LayoutPoint> {
  return new Map(nodes.map((node) => [node.id, { ...node.position }]))
}

export function applyPositions(
  nodes: Node[],
  positions: Map<string, LayoutPoint>,
): Node[] {
  return nodes.map((node) => {
    const next = positions.get(node.id)
    return next ? { ...node, position: next } : node
  })
}

export function findTransport(nodes: Node[]): Node | undefined {
  return nodes.find((node) => node.type === NODE_TYPES.TRANSPORT)
}

export function isCompactTransport(transport: Node): boolean {
  return Boolean((transport.data as { compact?: boolean } | undefined)?.compact)
}

export function transportWidth(transport: Node): number {
  return isCompactTransport(transport)
    ? TRANSPORT_NODE_WIDTH_COMPACT
    : TRANSPORT_NODE_WIDTH_BAR
}

export function transportHeight(transport: Node): number {
  return isCompactTransport(transport)
    ? TRANSPORT_NODE_HEIGHT_COMPACT
    : TRANSPORT_NODE_HEIGHT_BAR
}
