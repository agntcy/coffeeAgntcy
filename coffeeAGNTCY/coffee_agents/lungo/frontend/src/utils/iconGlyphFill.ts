/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Force SvgIcon glyph color via `fill` on the SVG and its paths.
 * OUK sets `MuiIconButton` `color="default"` to `brandIconPrimaryDefault`, which
 * `color`/`currentColor` alone cannot reliably override.
 */

import type { SystemStyleObject } from "@mui/system"

export function iconGlyphFillSx(
  fill: string,
  { important = false }: { important?: boolean } = {},
): SystemStyleObject {
  const value = important ? `${fill} !important` : fill

  return {
    color: value,
    fill: value,
    "& .MuiSvgIcon-root": {
      color: value,
      fill: value,
    },
    "& .MuiSvgIcon-root svg, & svg": {
      fill: value,
    },
    "& .MuiSvgIcon-root path, & svg path": {
      fill: value,
    },
  }
}
