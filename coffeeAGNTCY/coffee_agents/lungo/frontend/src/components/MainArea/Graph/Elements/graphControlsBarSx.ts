/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Compact graph control bar chrome — same surface as the graph canvas.
 */

import type { SxProps, Theme } from "@mui/material/styles"
import { mainAreaContentHorizontalPadding } from "../../mainAreaContentPadding"
import { getAppShellBackgroundColor } from "../../mainAreaBackground"

export const graphControlsBarSx: SxProps<Theme> = {
  display: "flex",
  flexShrink: 0,
  alignItems: "center",
  justifyContent: "space-between",
  width: "100%",
  px: mainAreaContentHorizontalPadding,
  py: 1,
  borderTop: "1px solid",
  borderColor: "divider",
  bgcolor: (theme) => getAppShellBackgroundColor(theme),
}
