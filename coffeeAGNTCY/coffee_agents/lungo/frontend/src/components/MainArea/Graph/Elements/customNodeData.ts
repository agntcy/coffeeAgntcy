/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Node } from "@xyflow/react"
import type { CustomNodeData, TransportNodeData } from "./types"

/** React Flow stores `node.data` as `Record<string, unknown>`; unwrap here once. */
export function customNodeDataFromNode(node: Node): CustomNodeData {
  return node.data as unknown as CustomNodeData
}

/** Serialize typed node payload for React Flow's `Node.data` field. */
export function flowNodeDataRecord(
  data: CustomNodeData | TransportNodeData,
): Record<string, unknown> {
  return data as unknown as Record<string, unknown>
}

/** Minimal {@link CustomNodeData} for tests; override fields via partial. */
export function customNodeDataFixture(
  over: Partial<CustomNodeData> = {},
): CustomNodeData {
  return {
    icon: null,
    label: "",
    label_subtitle: "",
    handles: "all",
    ...over,
  } as CustomNodeData
}
