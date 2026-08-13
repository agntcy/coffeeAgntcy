/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared dialog title bar / close-button layout.
 */

import type { SxProps, Theme } from "@mui/material/styles"

export const dialogCloseIconButtonSx: SxProps<Theme> = {
  position: "absolute",
  right: 8,
  top: 8,
}

/** Room for the absolute close button inside the dialog title bar. */
export const dialogTitleSx: SxProps<Theme> = {
  pr: 6,
  position: "relative",
}
