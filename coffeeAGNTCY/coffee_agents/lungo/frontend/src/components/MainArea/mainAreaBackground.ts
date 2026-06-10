/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Graph canvas background — contrasts with Sidebar and ChatArea (`background.paper`).
 * OUK `agentcyBlue` (`#187adc`) at 10% opacity.
 */

import { alpha, type Theme } from "@mui/material/styles"

export function getMainAreaBackgroundColor(theme: Theme): string {
  return alpha(theme.palette.vars.agentcyBlue, 0.1)
}
