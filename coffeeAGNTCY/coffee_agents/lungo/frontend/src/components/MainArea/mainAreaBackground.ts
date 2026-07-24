/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared background for the workflow sidebar and graph canvas (MainArea / React Flow).
 * OUK light mode: `theme.palette.background.paper` (Ft palette 100).
 */

import { alpha, type Theme } from "@mui/material/styles"

export function getAppShellBackgroundColor(theme: Theme): string {
  return theme.palette.background.paper
}

/** Frosted overlay for graph loading/error states over the canvas. */
export function getAppShellOverlayBackgroundColor(theme: Theme): string {
  return alpha(getAppShellBackgroundColor(theme), 0.1)
}
