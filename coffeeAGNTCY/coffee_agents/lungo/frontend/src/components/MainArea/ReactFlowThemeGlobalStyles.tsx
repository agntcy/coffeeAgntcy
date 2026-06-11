/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * React Flow ships class-based styles; plain CSS cannot read the MUI/OUK theme.
 * React Flow control panel position only; buttons use OUK `IconButton` + `Tooltip`.
 * Edge/marker colors are set on `CustomEdge` / `BranchingEdge` (avoid global CSS overriding SVG fills).
 */

import GlobalStyles from "@mui/material/GlobalStyles"
import type { Theme } from "@mui/material/styles"

import { getMainAreaBackgroundColor } from "./mainAreaBackground"

function reactFlowGlobalStyles(theme: Theme) {
  const mainAreaBackground = getMainAreaBackgroundColor(theme)

  return {
    ".react-flow": {
      background: mainAreaBackground,
    },
    ".react-flow__pane": {
      background: `${mainAreaBackground} !important`,
    },
    ".react-flow__controls": {
      bottom: `${theme.spacing(5)} !important`,
      left: `${theme.spacing(2)} !important`,
      right: "auto !important",
      width: "auto !important",
      maxWidth: "none !important",
      display: "flex !important",
      flexDirection: "column !important",
      alignItems: "flex-start !important",
      justifyContent: "center !important",
      margin: 0,
      padding: 0,
      background: `${theme.palette.background.paper} !important`,
      border: `1px solid ${theme.palette.divider} !important`,
      borderRadius:
        typeof theme.shape.borderRadius === "number"
          ? `${theme.shape.borderRadius}px`
          : `${theme.shape.borderRadius}`,
      boxShadow: "none !important",
    },
  }
}

export function ReactFlowThemeGlobalStyles() {
  return <GlobalStyles styles={(theme) => reactFlowGlobalStyles(theme)} />
}
