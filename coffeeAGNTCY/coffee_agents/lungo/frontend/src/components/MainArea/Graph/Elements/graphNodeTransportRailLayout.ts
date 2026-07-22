/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared TransportRail layout for CustomNode (conditional rail + padding).
 */

import {
  CUSTOM_NODE_INNER_WIDTH,
  CUSTOM_NODE_INNER_WIDTH_WITH_RAIL,
  GRAPH_NODE_PADDING_X,
  GRAPH_NODE_PADDING_X_WITH_RAIL,
} from "@/utils/graphNodeDimensions"
import type { AgentTransport } from "./transportMeta"

export function hasGraphNodeTransportRail(
  transportInterfaces?: AgentTransport[],
): boolean {
  return Boolean(transportInterfaces?.length)
}

export function graphNodePaddingX(
  transportInterfaces?: AgentTransport[],
): number {
  return hasGraphNodeTransportRail(transportInterfaces)
    ? GRAPH_NODE_PADDING_X_WITH_RAIL
    : GRAPH_NODE_PADDING_X
}

export function customNodeInnerWidth(
  transportInterfaces?: AgentTransport[],
): number {
  return hasGraphNodeTransportRail(transportInterfaces)
    ? CUSTOM_NODE_INNER_WIDTH_WITH_RAIL
    : CUSTOM_NODE_INNER_WIDTH
}
