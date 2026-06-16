/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Default graph canvas view (diagnostics capture). Used for initial load and Fit View.
 *
 * Fit zoom: `rawFitZoom * GRAPH_FIT_ZOOM_RATIO`
 **/

import type { FitViewOptions, Viewport } from "@xyflow/react"

/** Ratio applied to raw fitView zoom (initial load + Fit View). */
export const GRAPH_FIT_ZOOM_RATIO = 0.632015625

/** Converts {@link GRAPH_FIT_ZOOM_RATIO} to defaultViewport absolute zoom. */
const GRAPH_VIEWPORT_ZOOM_PER_FIT_RATIO = 0.824265304978623

/** Passed to `fitView()` together with computed minZoom/maxZoom. */
export const GRAPH_DEFAULT_FIT_VIEW_OPTIONS = {
  padding: 0,
  duration: 200,
} as const satisfies Pick<FitViewOptions, "padding" | "duration">

/** React Flow canvas zoom limits. */
export const GRAPH_MIN_ZOOM = 0.15
export const GRAPH_MAX_ZOOM = 1.8

/**
 * Fallback before nodes are measured / fitView runs (overridden by applyDefaultGraphView).
 */
export const GRAPH_DEFAULT_VIEWPORT: Viewport = {
  x: 0,
  y: 0,
  zoom: GRAPH_FIT_ZOOM_RATIO * GRAPH_VIEWPORT_ZOOM_PER_FIT_RATIO,
}
