/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { FitViewOptions, Viewport } from "@xyflow/react"

export const GRAPH_FIT_ZOOM_RATIO = 0.632015625
const GRAPH_VIEWPORT_ZOOM_PER_FIT_RATIO = 0.824265304978623

export const GRAPH_DEFAULT_FIT_VIEW_OPTIONS = {
  padding: 0,
  duration: 200,
} as const satisfies Pick<FitViewOptions, "padding" | "duration">

export const GRAPH_MIN_ZOOM = 0.15
export const GRAPH_MAX_ZOOM = 1.8

export const GRAPH_DEFAULT_VIEWPORT: Viewport = {
  x: 0,
  y: 0,
  zoom: GRAPH_FIT_ZOOM_RATIO * GRAPH_VIEWPORT_ZOOM_PER_FIT_RATIO,
}
