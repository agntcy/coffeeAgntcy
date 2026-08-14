/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Top title bar uses light-theme chrome in both app color modes (see corto exchange nav).
 */

import { alpha, type Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import { lightVars } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

/**
 * Fixed light nav surface - not tied to active MUI color mode.
 * Uses OUK light semantic tokens (same values as theme.palette.vars in light mode).
 */
export function getLungoNavHeaderColors(theme: Theme) {
  return {
    background: lightVars.baseBackgroundStrong,
    border: theme.palette.grey[300],
    icon: lightVars.brandIconPrimaryDefault,
  } as const
}

/** OUK `Header` fixed height (`getHeaderStyles`). */
export const LUNGO_NAV_HEADER_HEIGHT_PX = 56

export function navigationHeaderSx(theme: Theme): SystemStyleObject<Theme> {
  const { background, border } = getLungoNavHeaderColors(theme)

  return {
    bgcolor: `${background} !important`,
    backgroundColor: `${background} !important`,
    borderBottom: `1px solid ${border} !important`,
  }
}

export function navigationHeaderIconButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  const { icon } = getLungoNavHeaderColors(theme)
  const iconHoverFill = alpha(icon, 0.08)

  return {
    ...iconGlyphFillSx(icon, { important: true }),
    "&:hover": {
      bgcolor: iconHoverFill,
      backgroundColor: iconHoverFill,
    },
  }
}
