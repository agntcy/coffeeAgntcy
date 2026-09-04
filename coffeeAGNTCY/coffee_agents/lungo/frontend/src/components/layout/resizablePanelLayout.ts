/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared react-resizable-panels layout tokens.
 */

/** Drag handle thickness in pixels (horizontal or vertical separator). */
export const RESIZABLE_PANEL_SEPARATOR_SIZE_PX = 4

/**
 * Touch padding overlaps the adjacent panel (negative margin) so layout stays
 * RESIZABLE_PANEL_SEPARATOR_SIZE_PX while the grab target is wider.
 */
export const RESIZABLE_PANEL_SEPARATOR_TOUCH_PADDING_PX = 8

/** Max share of a split group for the resizable panel (sidebar or chat). */
export const RESIZABLE_PANEL_MAX_SIZE = "75%"

/** Min share kept for the adjacent panel (main column or graph). */
export const RESIZABLE_PANEL_MIN_SIZE = "25%"
