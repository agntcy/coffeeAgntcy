/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Layout dimensions for graph nodes — must match CustomNode / TransportNode DOM.
 */

import type { Node } from "@xyflow/react"

/** CustomNode / TransportNode root `px` (theme spacing units per side). */
export const GRAPH_NODE_PADDING_X = 2

/** Graph node root `px` when a TransportRail is shown (doubled). */
export const GRAPH_NODE_PADDING_X_WITH_RAIL = 4

/** Graph node root `py` (theme spacing units per side). */
export const GRAPH_NODE_PADDING_Y = 2

/** Graph node root horizontal inset at default padding (px: 2). */
export const CUSTOM_NODE_HORIZONTAL_PADDING = 32

/** Graph node root horizontal inset when TransportRail is shown (px: 4). */
export const CUSTOM_NODE_HORIZONTAL_PADDING_WITH_RAIL = 64

/** Outer custom card width for layout and React Flow positioning. */
export const CUSTOM_NODE_WIDTH = 230

/** Inner text column at default padding — matches label widths in CustomNode. */
export const CUSTOM_NODE_INNER_WIDTH =
  CUSTOM_NODE_WIDTH - CUSTOM_NODE_HORIZONTAL_PADDING

/** Inner text column when TransportRail is shown. */
export const CUSTOM_NODE_INNER_WIDTH_WITH_RAIL =
  CUSTOM_NODE_WIDTH - CUSTOM_NODE_HORIZONTAL_PADDING_WITH_RAIL

/** Outer custom card height — icon, labels, and vertical padding. */
export const CUSTOM_NODE_HEIGHT = 120

/** Horizontal gap between custom cards in the same row. */
export const CUSTOM_NODE_X_GAP = 300

/** Circular compact transport — keep in sync with transportNode.tsx. */
export const TRANSPORT_NODE_WIDTH_COMPACT = 176
export const TRANSPORT_NODE_HEIGHT_COMPACT = 176

/** Bar transport — keep in sync with transportNode.tsx. */
export const TRANSPORT_NODE_WIDTH_BAR = 1200
export const TRANSPORT_NODE_HEIGHT_BAR = 52

/** Horizontal padding inside logistics group containers. */
export const GROUP_CONTENT_PADDING_X = 96

/** Vertical padding inside logistics group containers. */
export const GROUP_CONTENT_PADDING_Y = 48

/** Buckets nearby Y values into the same layout row. */
export const LAYER_Y_BUCKET = 80

/** Card center X — side icons sit outside the card box. */
export function customNodeCardCenterX(position: { x: number }): number {
  return position.x + CUSTOM_NODE_WIDTH / 2
}

/** Card center Y. */
export function customNodeCardCenterY(position: { y: number }): number {
  return position.y + CUSTOM_NODE_HEIGHT / 2
}

/** Horizontal center of a transport node (bar or compact). */
export function transportCenterX(transport: Node): number {
  const compact = Boolean(
    (transport.data as { compact?: boolean } | undefined)?.compact,
  )
  const width = compact
    ? TRANSPORT_NODE_WIDTH_COMPACT
    : TRANSPORT_NODE_WIDTH_BAR
  return transport.position.x + width / 2
}
