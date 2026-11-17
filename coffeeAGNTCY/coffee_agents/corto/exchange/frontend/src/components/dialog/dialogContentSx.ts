/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { SxProps, Theme } from "@mui/material/styles"

export const dialogContentSx: SxProps<Theme> = {
  px: "24px",
  py: "16px",
  borderTop: (theme) => `1px solid ${theme.palette.vars.controlBorderDefault}`,
}
