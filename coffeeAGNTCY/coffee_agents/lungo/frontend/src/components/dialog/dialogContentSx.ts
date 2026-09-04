/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * OUK DialogContent sets padding: 0 for full-bleed layouts; Lungo dialogs
 * keep MUI's default dialog body inset instead. Title/body bar is a content
 * borderTop (MUI `dividers` would also paint a body/footer bar).
 */

import type { SxProps, Theme } from "@mui/material/styles"

export const dialogContentSx: SxProps<Theme> = {
  px: "24px",
  py: "16px",
  borderTop: (theme) => `1px solid ${theme.palette.vars.controlBorderDefault}`,
}
