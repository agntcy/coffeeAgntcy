/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Default graph canvas view — captured via graph controls → "Log fitView settings"
 * (last diagnostics session: zoomScaleVsRawFit ≈ 0.9099).
 *
 * Zoom is applied as `rawFitZoom * GRAPH_VIEW_ZOOM_SCALE_VS_RAW_FIT` so it adapts
 * to the live `.react-flow` container size and current node bounds.
 **/

import type { FitViewOptions, Viewport } from "@xyflow/react"

/** currentZoom / rawFitZoom at padding 0 (from last console capture). */
export const GRAPH_VIEW_ZOOM_SCALE_VS_RAW_FIT = 0.9099

/** Passed to `fitView()` together with computed minZoom/maxZoom. */
export const GRAPH_VIEW_DEFAULT_FIT_VIEW_OPTIONS = {
  padding: 0,
  duration: 300,
} as const satisfies Pick<FitViewOptions, "padding" | "duration">

/** React Flow canvas zoom limits. */
export const GRAPH_MIN_ZOOM = 0.15
export const GRAPH_MAX_ZOOM = 1.8

/**
 * Fallback before nodes are measured / fitView runs (overridden by applyDefaultGraphView).
 */
export const GRAPH_VIEW_DEFAULT_VIEWPORT: Viewport = {
  x: 0,
  y: 0,
  zoom: 0.75,
}
