/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Chat panel surface — slightly darker than sidebar/canvas (`background.paper`).
 * OUK light mode: `background.default` (Ft palette 200, #eff3fc).
 */

import type { Theme } from "@mui/material/styles"

export function getChatAreaBackgroundColor(theme: Theme): string {
  return theme.palette.background.default
}
