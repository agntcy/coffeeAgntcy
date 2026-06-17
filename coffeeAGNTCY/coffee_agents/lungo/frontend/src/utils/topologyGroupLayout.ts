/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Node } from "@xyflow/react"
import { NODE_TYPES } from "@/utils/const"
import {
  bucketNodeLayerY,
  CUSTOM_NODE_HEIGHT,
  CUSTOM_NODE_WIDTH,
  CUSTOM_NODE_X_GAP,
  TRANSPORT_NODE_HEIGHT_COMPACT,
  TRANSPORT_NODE_WIDTH_BAR,
  TRANSPORT_NODE_WIDTH_COMPACT,
} from "./topologyLayout"

const GROUP_CONTENT_PADDING = 48
const TRANSPORT_NODE_HEIGHT_BAR = 52

function parseGroupStyleWidth(
  style: { width?: unknown } | undefined,
): number | null {
  const width = style?.width
  if (typeof width === "number" && Number.isFinite(width)) return width
  if (typeof width === "string") {
    const parsed = Number.parseFloat(width)
    if (Number.isFinite(parsed)) return parsed
  }
  return null
}

function nodeLayoutWidth(node: Node): number {
  if (node.type === NODE_TYPES.TRANSPORT) {
    const compact = Boolean(
      (node.data as { compact?: boolean } | undefined)?.compact,
    )
    return compact ? TRANSPORT_NODE_WIDTH_COMPACT : TRANSPORT_NODE_WIDTH_BAR
  }
  if (node.type === NODE_TYPES.CUSTOM) {
    return CUSTOM_NODE_WIDTH
  }
  return CUSTOM_NODE_WIDTH
}

function nodeLayoutHeight(node: Node): number {
  if (node.type === NODE_TYPES.TRANSPORT) {
    const compact = Boolean(
      (node.data as { compact?: boolean } | undefined)?.compact,
    )
    return compact ? TRANSPORT_NODE_HEIGHT_COMPACT : TRANSPORT_NODE_HEIGHT_BAR
  }
  return CUSTOM_NODE_HEIGHT
}

/**
 * Shrinks the group container to its children and pads evenly so fitView centers
 * the graph instead of leaving empty margin inside a wide group box.
 * Uses card/body sizes only — side icons are excluded from bounds.
 */
export function fitGroupContainerToContent(nodes: Node[]): Node[] {
  const group = nodes.find((node) => node.type === NODE_TYPES.GROUP)
  if (!group) return nodes

  const children = nodes.filter((node) => node.parentId === group.id)
  if (children.length === 0) return nodes

  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity

  for (const child of children) {
    const width = nodeLayoutWidth(child)
    const height = nodeLayoutHeight(child)
    minX = Math.min(minX, child.position.x)
    minY = Math.min(minY, child.position.y)
    maxX = Math.max(maxX, child.position.x + width)
    maxY = Math.max(maxY, child.position.y + height)
  }

  const contentWidth = maxX - minX
  const contentHeight = maxY - minY
  const shiftX = GROUP_CONTENT_PADDING - minX
  const shiftY = GROUP_CONTENT_PADDING - minY
  const newGroupWidth = contentWidth + GROUP_CONTENT_PADDING * 2
  const newGroupHeight = contentHeight + GROUP_CONTENT_PADDING * 2

  return nodes.map((node) => {
    if (node.id === group.id) {
      return {
        ...node,
        style: {
          ...node.style,
          width: newGroupWidth,
          height: newGroupHeight,
        },
      }
    }
    if (node.parentId === group.id) {
      return {
        ...node,
        position: {
          x: node.position.x + shiftX,
          y: node.position.y + shiftY,
        },
      }
    }
    return node
  })
}

/**
 * Centers a single child (e.g. compact transport) horizontally in its parent group.
 * Other children are shifted by the same delta so relative positions are preserved.
 */
export function centerGroupChildrenOnChildX(
  nodes: Node[],
  childId: string,
  childWidth: number,
): Node[] {
  const child = nodes.find((node) => node.id === childId)
  if (!child?.parentId) return nodes

  const group = nodes.find(
    (node) => node.id === child.parentId && node.type === NODE_TYPES.GROUP,
  )
  const groupWidth = parseGroupStyleWidth(group?.style)
  if (groupWidth == null) return nodes

  const childCenterX = child.position.x + childWidth / 2
  const dx = groupWidth / 2 - childCenterX
  if (Math.abs(dx) < 0.01) return nodes

  return nodes.map((node) =>
    node.parentId === child.parentId
      ? {
          ...node,
          position: { ...node.position, x: node.position.x + dx },
        }
      : node,
  )
}

/**
 * Lays out custom nodes per row inside the group with equal left/right margins
 * and even spacing between cards. Transport position is not changed.
 */
export function layoutCustomNodesInGroupSymmetric(
  nodes: Node[],
  transportId: string,
): Node[] {
  const group = nodes.find((node) => node.type === NODE_TYPES.GROUP)
  if (!group) return nodes

  const groupWidth = parseGroupStyleWidth(group.style)
  if (groupWidth == null) return nodes

  const customChildren = nodes.filter(
    (node) =>
      node.parentId === group.id &&
      node.type === NODE_TYPES.CUSTOM &&
      node.id !== transportId,
  )
  if (customChildren.length === 0) return nodes

  const positions = new Map(
    nodes.map((node) => [node.id, { ...node.position }]),
  )

  const byLayer = new Map<number, string[]>()
  for (const node of customChildren) {
    const layer = bucketNodeLayerY(node.position.y)
    if (!byLayer.has(layer)) byLayer.set(layer, [])
    byLayer.get(layer)!.push(node.id)
  }

  for (const ids of byLayer.values()) {
    const sorted = [...ids].sort(
      (a, b) => positions.get(a)!.x - positions.get(b)!.x,
    )
    const count = sorted.length
    const contentSpan = (count - 1) * CUSTOM_NODE_X_GAP + CUSTOM_NODE_WIDTH
    const leftMargin = (groupWidth - contentSpan) / 2
    sorted.forEach((id, index) => {
      const point = positions.get(id)!
      positions.set(id, {
        x: leftMargin + index * CUSTOM_NODE_X_GAP,
        y: point.y,
      })
    })
  }

  return nodes.map((node) => {
    if (node.id === transportId) return node
    const next = positions.get(node.id)
    return next ? { ...node, position: next } : node
  })
}

/**
 * Single-pass compact group layout: sizes the group from symmetric row spans,
 * centers each custom row and the transport with equal padding, and normalizes Y.
 */
export function layoutCompactGroupSymmetric(
  nodes: Node[],
  transportId: string,
): Node[] {
  const group = nodes.find((node) => node.type === NODE_TYPES.GROUP)
  if (!group) return nodes

  const transport = nodes.find((node) => node.id === transportId)
  if (!transport?.parentId || transport.parentId !== group.id) return nodes

  const customChildren = nodes.filter(
    (node) =>
      node.parentId === group.id &&
      node.type === NODE_TYPES.CUSTOM &&
      node.id !== transportId,
  )
  if (customChildren.length === 0) return nodes

  const positions = new Map(
    nodes.map((node) => [node.id, { ...node.position }]),
  )

  const byLayer = new Map<number, string[]>()
  for (const node of customChildren) {
    const layer = bucketNodeLayerY(node.position.y)
    if (!byLayer.has(layer)) byLayer.set(layer, [])
    byLayer.get(layer)!.push(node.id)
  }

  let contentWidth = TRANSPORT_NODE_WIDTH_COMPACT
  for (const ids of byLayer.values()) {
    const span = (ids.length - 1) * CUSTOM_NODE_X_GAP + CUSTOM_NODE_WIDTH
    contentWidth = Math.max(contentWidth, span)
  }
  const groupWidth = contentWidth + GROUP_CONTENT_PADDING * 2

  for (const ids of byLayer.values()) {
    const sorted = [...ids].sort(
      (a, b) => positions.get(a)!.x - positions.get(b)!.x,
    )
    const layerSpan =
      (sorted.length - 1) * CUSTOM_NODE_X_GAP + CUSTOM_NODE_WIDTH
    const layerLeft = GROUP_CONTENT_PADDING + (contentWidth - layerSpan) / 2
    sorted.forEach((id, index) => {
      const point = positions.get(id)!
      positions.set(id, {
        x: layerLeft + index * CUSTOM_NODE_X_GAP,
        y: point.y,
      })
    })
  }

  const transportPos = positions.get(transportId)!
  positions.set(transportId, {
    x:
      GROUP_CONTENT_PADDING + (contentWidth - TRANSPORT_NODE_WIDTH_COMPACT) / 2,
    y: transportPos.y,
  })

  const groupChildIds = new Set(
    [...customChildren, transport].map((node) => node.id),
  )
  let minY = Infinity
  let maxY = -Infinity
  for (const id of groupChildIds) {
    const pos = positions.get(id)!
    const height =
      id === transportId ? TRANSPORT_NODE_HEIGHT_COMPACT : CUSTOM_NODE_HEIGHT
    minY = Math.min(minY, pos.y)
    maxY = Math.max(maxY, pos.y + height)
  }
  const shiftY = GROUP_CONTENT_PADDING - minY
  const groupHeight = maxY - minY + GROUP_CONTENT_PADDING * 2

  for (const id of groupChildIds) {
    const pos = positions.get(id)!
    positions.set(id, { x: pos.x, y: pos.y + shiftY })
  }

  return nodes.map((node) => {
    if (node.id === group.id) {
      return {
        ...node,
        style: {
          ...node.style,
          width: groupWidth,
          height: groupHeight,
        },
      }
    }
    if (node.parentId === group.id) {
      const next = positions.get(node.id)
      return next ? { ...node, position: next } : node
    }
    return node
  })
}
