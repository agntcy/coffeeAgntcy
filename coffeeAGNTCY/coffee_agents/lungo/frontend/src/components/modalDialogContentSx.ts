/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * OUK DialogContent sets padding: 0 for full-bleed layouts; modals in this app
 * keep MUI's default dialog body inset instead.
 */

import type { SxProps, Theme } from "@mui/material/styles"

export const modalDialogContentSx: SxProps<Theme> = {
  px: "24px",
  py: "16px",
}
