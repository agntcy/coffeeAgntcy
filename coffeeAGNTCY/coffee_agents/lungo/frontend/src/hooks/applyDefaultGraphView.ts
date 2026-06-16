/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { FitViewOptions, Node, Rect } from "@xyflow/react"
import { getViewportForBounds } from "@xyflow/react"
import {
  GRAPH_MAX_ZOOM,
  GRAPH_MIN_ZOOM,
  GRAPH_DEFAULT_FIT_VIEW_OPTIONS,
  GRAPH_FIT_ZOOM_RATIO,
} from "@/config/graphViewDefaults"

export const measureGraphContainerSize = (): {
  width: number
  height: number
} | null => {
  const graphEl = document.querySelector<HTMLElement>(".react-flow")
  if (graphEl === null) {
    return null
  }

  const { width, height } = graphEl.getBoundingClientRect()
  if (width <= 0 || height <= 0) {
    return null
  }

  return { width, height }
}

export const computeDefaultFitViewZoom = (
  bounds: Rect,
  containerWidth: number,
  containerHeight: number,
): number => {
  const rawFit = getViewportForBounds(
    bounds,
    containerWidth,
    containerHeight,
    GRAPH_MIN_ZOOM,
    GRAPH_MAX_ZOOM,
    GRAPH_DEFAULT_FIT_VIEW_OPTIONS.padding,
  )

  return Math.min(
    Math.max(rawFit.zoom * GRAPH_FIT_ZOOM_RATIO, GRAPH_MIN_ZOOM),
    GRAPH_MAX_ZOOM,
  )
}

interface ApplyDefaultGraphViewDeps {
  fitView: (options?: FitViewOptions) => Promise<boolean>
  getNodes: () => Node[]
  getNodesBounds: (nodes: Node[]) => Rect
}

/** Applies {@link GRAPH_DEFAULT_FIT_VIEW_OPTIONS} with zoom derived from live layout. */
export async function applyDefaultGraphView({
  fitView,
  getNodes,
  getNodesBounds,
}: ApplyDefaultGraphViewDeps): Promise<void> {
  const container = measureGraphContainerSize()
  const nodes = getNodes()
  if (container === null || nodes.length === 0) {
    return
  }

  const bounds = getNodesBounds(nodes)
  const targetZoom = computeDefaultFitViewZoom(
    bounds,
    container.width,
    container.height,
  )

  await fitView({
    ...GRAPH_DEFAULT_FIT_VIEW_OPTIONS,
    minZoom: targetZoom,
    maxZoom: targetZoom,
  })
}
