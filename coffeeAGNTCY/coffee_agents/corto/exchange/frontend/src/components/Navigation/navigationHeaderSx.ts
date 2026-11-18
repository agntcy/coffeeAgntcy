/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Top title bar uses light-theme chrome in both app color modes.
 */

import { alpha, type Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import { lightVars } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

export function getCortoNavHeaderColors(theme: Theme) {
  return {
    background: lightVars.baseBackgroundStrong,
    border: theme.palette.grey[300],
    icon: lightVars.brandIconPrimaryDefault,
  } as const
}

/** OUK `Header` fixed height. */
export const CORTO_NAV_HEADER_HEIGHT_PX = 56

export function navigationHeaderSx(theme: Theme): SystemStyleObject<Theme> {
  const { background, border } = getCortoNavHeaderColors(theme)

  return {
    bgcolor: `${background} !important`,
    backgroundColor: `${background} !important`,
    borderBottom: `1px solid ${border} !important`,
  }
}

export function navigationHeaderIconButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  const { icon } = getCortoNavHeaderColors(theme)
  const iconHoverFill = alpha(icon, 0.08)

  return {
    ...iconGlyphFillSx(icon, { important: true }),
    "&:hover": {
      bgcolor: iconHoverFill,
      backgroundColor: iconHoverFill,
    },
  }
}
