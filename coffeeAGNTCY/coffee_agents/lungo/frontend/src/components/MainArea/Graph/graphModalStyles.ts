/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared `sx` fragments for graph-related panels (JSON blocks, loading overlays).
 * Positioned portal/backdrop styles were removed in favor of OUK `Dialog` / `IconButtonDropdown`.
 */

import { alpha } from "@mui/material/styles"
import type { SxProps, Theme } from "@mui/material/styles"

export const graphModalScrollBodySx: SxProps<Theme> = {
  position: "relative",
  display: "flex",
  maxHeight: "min(40vh, 320px)",
  minHeight: 0,
  width: "100%",
  flexDirection: "column",
  gap: 1.5,
  overflowY: "auto",
}

export const graphModalPreSx: SxProps<Theme> = {
  overflow: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  borderRadius: 1,
  border: "1px solid",
  borderColor: "divider",
  p: 1.5,
  fontFamily: "monospace",
  fontSize: "0.75rem",
  lineHeight: 1.5,
  color: "text.primary",
}

export const graphModalLoadingOverlaySx: SxProps<Theme> = {
  position: "absolute",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  bgcolor: (theme) => alpha(theme.palette.background.paper, 0.85),
  backdropFilter: "blur(8px)",
}

export const graphModalFieldCardSx: SxProps<Theme> = {
  borderRadius: 1,
  border: "1px solid",
  borderColor: "divider",
  p: 1.5,
}
