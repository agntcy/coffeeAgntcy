/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import type { GraphConfig } from "@/utils/graphConfigs"

/** Build a GraphConfig snapshot from live React Flow state (e.g. agentic API topology). */
export function graphConfigFromNodes(
  title: string,
  nodes: Node[],
  edges: Edge[],
  animationSequence: GraphConfig["animationSequence"],
): GraphConfig {
  return {
    title,
    nodes,
    edges,
    animationSequence,
  }
}
