/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"

/**
 * Neutralize OUK primary `:active` layout shift (border + padding shrink).
 * Resting size stays on OUK defaults; only press state is overridden.
 */
export function composerPrimaryButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  const activeBorderColor = theme.palette.vars.interactivePrimaryDefaultDefault

  return {
    "&.MuiButton-sizeMedium.MuiButton-primary": {
      "&:active": {
        border: "none",
        outline: `1px solid ${activeBorderColor}`,
        outlineOffset: "-1px",
        paddingLeft: "16px",
        paddingRight: "16px",
      },
    },
  }
}
