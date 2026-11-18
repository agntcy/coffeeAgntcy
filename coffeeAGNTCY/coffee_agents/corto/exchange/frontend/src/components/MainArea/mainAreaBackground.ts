/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared background for the workflow sidebar and graph canvas (MainArea / React Flow).
 */

import type { Theme } from "@mui/material/styles"

export function getAppShellBackgroundColor(theme: Theme): string {
  return theme.palette.background.paper
}
