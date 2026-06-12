/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared styles for accessibility patterns (visually hidden text, skip links).
 */

import type { SxProps, Theme } from "@mui/material/styles"

/** Hide visually; keep available to screen readers and associated controls. */
export const visuallyHiddenSx: SxProps<Theme> = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0, 0, 0, 0)",
  whiteSpace: "nowrap",
  border: 0,
}

/** Skip link: off-screen until keyboard focus. */
export const skipLinkSx: SxProps<Theme> = {
  position: "absolute",
  left: -10000,
  top: "auto",
  width: 1,
  height: 1,
  overflow: "hidden",
  zIndex: 1300,
  px: 2,
  py: 1,
  typography: "body2",
  color: "primary.contrastText",
  bgcolor: "primary.main",
  borderRadius: 1,
  textDecoration: "none",
  "&:focus": {
    left: 8,
    top: 8,
    width: "auto",
    height: "auto",
    overflow: "visible",
  },
}
