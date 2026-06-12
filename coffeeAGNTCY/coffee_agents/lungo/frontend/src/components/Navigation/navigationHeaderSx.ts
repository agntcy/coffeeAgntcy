/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Top title bar uses light-theme chrome in both app color modes (see corto exchange nav).
 */

import type { Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

/** Fixed light nav surface — not tied to active MUI color mode. */
export const LUNGO_NAV_HEADER_COLORS = {
  background: "#eff3fc",
  border: "#dbe0e5",
  icon: "#1d69cc",
} as const

export function navigationHeaderSx(): SystemStyleObject<Theme> {
  const { background, border } = LUNGO_NAV_HEADER_COLORS

  return {
    bgcolor: `${background} !important`,
    backgroundColor: `${background} !important`,
    borderBottom: `1px solid ${border} !important`,
  }
}

export function navigationHeaderIconButtonSx(): SystemStyleObject<Theme> {
  return {
    ...iconGlyphFillSx(LUNGO_NAV_HEADER_COLORS.icon, { important: true }),
    "&:hover": {
      bgcolor: "rgba(29, 105, 204, 0.08)",
      backgroundColor: "rgba(29, 105, 204, 0.08)",
    },
  }
}
