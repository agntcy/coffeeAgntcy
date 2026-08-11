/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Success icon fill on paper surfaces. OUK success.main (green500) is ~2.52:1 on
 * white; use green800 in light mode until upstream A2 is fixed (see contrast-audit.md).
 */

import { green800 } from "@open-ui-kit/core"
import type { Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"

/** ≥3:1 on white (UI component AA). Dark mode keeps success.main (~5.9:1 on paper). */
export function getSuccessIconColor(theme: Theme): string {
  return theme.palette.mode === "light" ? green800 : theme.palette.success.main
}

export function successIconColorSx(theme: Theme): SystemStyleObject<Theme> {
  return { color: getSuccessIconColor(theme) }
}
