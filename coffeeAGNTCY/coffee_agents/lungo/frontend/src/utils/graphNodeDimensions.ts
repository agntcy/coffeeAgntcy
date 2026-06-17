/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Layout dimensions for graph nodes — must match CustomNode / TransportNode DOM.
 */

import type { Node } from "@xyflow/react"

/** CustomNode root `p: 2` horizontal inset (theme.spacing(2) × 2). */
export const CUSTOM_NODE_HORIZONTAL_PADDING = 32

/** Outer custom card width for layout and React Flow positioning. */
export const CUSTOM_NODE_WIDTH = 230

/** Inner text column — matches label widths in CustomNode. */
export const CUSTOM_NODE_INNER_WIDTH =
  CUSTOM_NODE_WIDTH - CUSTOM_NODE_HORIZONTAL_PADDING

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

/** Padding inside logistics group containers. */
export const GROUP_CONTENT_PADDING = 48

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
