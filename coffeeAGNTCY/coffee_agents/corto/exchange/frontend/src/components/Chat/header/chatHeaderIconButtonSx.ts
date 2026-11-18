/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Theme } from "@mui/material/styles"
import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

export function chatHeaderIconButtonSx(theme: Theme) {
  return {
    width: 32,
    height: 32,
    minWidth: 32,
    padding: "6px",
    borderRadius: theme.shape.borderRadius,
    background: "none",
    backgroundColor: "transparent",
    boxShadow: "none",
    ...iconGlyphFillSx(theme.palette.vars.controlIconDefault, {
      important: true,
    }),
  }
}
