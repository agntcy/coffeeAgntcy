/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared graph node chrome (CustomNode, TransportNode): surfaces, borders,
 * and hover behavior using the active MUI / Open UI Kit theme palette.
 */

import type { CSSProperties } from "react"
import type { Theme } from "@mui/material/styles"
import { alpha } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import {
  getAssetPngIconBackground,
  getAssetPngIconSize,
  getGraphIconChipHoverBackground,
} from "@/utils/assetPngIcon"

export type GraphNodeSurfaceState = "default" | "active" | "selected"

/** OUK control icon fill (`#e8e9ea` in dark mode) — not `brandIconPrimaryDefault`. */
export function getControlIconColor(theme: Theme): string {
  return theme.palette.vars.controlIconDefault
}

export interface GraphNodeRootSurfaceOptions {
  /** Defaults to 2× theme.shape.borderRadius (typically 8px). */
  borderRadius?: string | number
}

function defaultCardRadius(theme: Theme): string | number {
  const r = theme.shape.borderRadius
  return typeof r === "number" ? r * 2 : r
}

function getGraphNodeRestingBackground(
  theme: Theme,
  state: GraphNodeSurfaceState,
): string {
  if (theme.palette.mode === "dark") {
    switch (state) {
      case "active":
      case "selected":
        return theme.palette.vars.controlBackgroundMedium
      default:
        return theme.palette.vars.baseBackgroundWeak
    }
  }

  switch (state) {
    case "active":
      return theme.palette.action.selected
    case "selected":
      return theme.palette.vars.baseBackgroundHover
    default:
      return theme.palette.background.default
  }
}

function getGraphNodeHoverBackground(
  theme: Theme,
  state: GraphNodeSurfaceState,
): string {
  if (theme.palette.mode === "dark") {
    if (state === "default") {
      return theme.palette.vars.controlBackgroundMedium
    }

    return theme.palette.vars.baseBorderMedium
  }

  if (state === "default") {
    return theme.palette.vars.baseBackgroundHover
  }

  return alpha(
    theme.palette.primary.main,
    theme.palette.action.selectedOpacity + theme.palette.action.focusOpacity,
  )
}

/**
 * Root node surface: palette-driven border/background, hover lift, and focus ring.
 * Merge with layout-only `sx` (width, flexDirection, etc.) in each node component.
 */
export function graphNodeRootSurfaceSx(
  theme: Theme,
  state: GraphNodeSurfaceState,
  options: GraphNodeRootSurfaceOptions = {},
): SystemStyleObject<Theme> {
  const borderRadius = options.borderRadius ?? defaultCardRadius(theme)
  const borderColor = theme.palette.divider
  const primary = theme.palette.primary.main
  const restingBg = getGraphNodeRestingBackground(theme, state)
  const hoverBg = getGraphNodeHoverBackground(theme, state)

  const restingOutline =
    state === "active"
      ? `2px solid ${alpha(primary, 0.45)}`
      : state === "selected"
        ? `2px solid ${primary}`
        : "none"

  const restingShadow =
    state === "active" || state === "selected" ? theme.shadows[4] : "none"

  return {
    border: "1px solid",
    borderColor,
    borderRadius,
    bgcolor: restingBg,
    color: theme.palette.text.primary,
    outline: restingOutline,
    boxShadow: restingShadow,
    // Do not animate border-color or outline — tweening between divider and
    // primary reads as a flash; outline from "none" also flickers cross-browser.
    transition: theme.transitions.create(["background-color", "box-shadow"], {
      duration: theme.transitions.duration.shortest,
    }),
    "&:hover": {
      bgcolor: hoverBg,
      boxShadow: theme.shadows[6],
      outline: `2px solid ${primary}`,
      borderColor: alpha(primary, 0.45),
    },
  }
}

/**
 * Shared chip for graph icons (MUI SvgIcon, PNG, SVG): theme background, divider border,
 * and `theme.shape.borderRadius` (MUI IconButton uses 50% but has no border/background).
 */
export function graphIconChipSx(theme: Theme): SystemStyleObject<Theme> {
  const iconSize = getAssetPngIconSize(theme)

  return {
    overflow: "hidden",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: iconSize,
    height: iconSize,
    flexShrink: 0,
    boxSizing: "content-box",
    bgcolor: getAssetPngIconBackground(theme),
    border: "1px solid",
    borderColor: theme.palette.divider,
    borderRadius: (theme.shape.borderRadius as number) * 0.25,
    "& .MuiSvgIcon-root": {
      fontSize: iconSize,
    },
  }
}

/** Hover for interactive graph icon chips (IconButtons, auxiliary links). */
export function graphIconChipInteractiveHoverSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  const restingBg = getAssetPngIconBackground(theme)
  const hoverBg = getGraphIconChipHoverBackground(theme)

  return {
    bgcolor: restingBg,
    transition: theme.transitions.create("background-color", {
      duration: theme.transitions.duration.shortest,
      easing: theme.transitions.easing.easeInOut,
    }),
    "&:hover": {
      bgcolor: hoverBg,
      // Override MUI IconButton semi-transparent hover overlay.
      backgroundColor: hoverBg,
      "@media (hover: none)": {
        bgcolor: restingBg,
        backgroundColor: restingBg,
      },
    },
  }
}

function graphIconButtonChipSx(theme: Theme): SystemStyleObject<Theme> {
  const iconButtonSize = theme.spacing(3)

  return {
    ...graphIconChipSx(theme),
    ...graphIconChipInteractiveHoverSx(theme),
    width: iconButtonSize,
    height: iconButtonSize,
    minWidth: iconButtonSize,
    padding: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    boxShadow: theme.shadows[1],
  }
}

/**
 * Graph node side IconButtons (GitHub, directory, identity checkmark).
 * Chip layout only — glyph color stays OUK default (`brandIconPrimaryDefault`, blue in light mode).
 */
export function graphSideIconButtonSx(theme: Theme): SystemStyleObject<Theme> {
  return graphIconButtonChipSx(theme)
}

export function graphSideIconButtonSxWithModal(
  theme: Theme,
): SystemStyleObject<Theme> {
  return graphSideIconButtonSx(theme)
}

/** GitHub / similar auxiliary link on nodes — same chip as {@link graphSideIconButtonSx}. */
export function graphNodeAuxiliaryControlSurfaceSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    ...graphSideIconButtonSx(theme),
    textDecoration: "none",
    cursor: "pointer",
  }
}

/** Fixed outer box for CustomNode / TransportNode side `button` and `a` icons. */
export const GRAPH_NODE_SIDE_ICON_SIZE = "1.6rem"

/** Inner glyph/image — fits inside {@link GRAPH_NODE_SIDE_ICON_SIZE} with 1px border. */
const GRAPH_NODE_SIDE_ICON_INNER_SIZE = "1.125rem"

/** Shared compact side control surface (no `graphIconButtonChipSx` padding/content-box). */
function graphNodeSideIconControlBaseSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    boxSizing: "border-box",
    ...graphIconChipInteractiveHoverSx(theme),
    bgcolor: getAssetPngIconBackground(theme),
    border: "1px solid",
    borderColor: theme.palette.divider,
    borderRadius: theme.shape.borderRadius,
    boxShadow: theme.shadows[1],
    minWidth: 0,
    width: GRAPH_NODE_SIDE_ICON_SIZE,
    height: GRAPH_NODE_SIDE_ICON_SIZE,
    maxWidth: GRAPH_NODE_SIDE_ICON_SIZE,
    maxHeight: GRAPH_NODE_SIDE_ICON_SIZE,
    padding: 0,
    overflow: "hidden",
    "&&": {
      minWidth: 0,
      width: GRAPH_NODE_SIDE_ICON_SIZE,
      height: GRAPH_NODE_SIDE_ICON_SIZE,
      padding: 0,
    },
    "& .MuiSvgIcon-root": {
      fontSize: GRAPH_NODE_SIDE_ICON_INNER_SIZE,
      width: GRAPH_NODE_SIDE_ICON_INNER_SIZE,
      height: GRAPH_NODE_SIDE_ICON_INNER_SIZE,
    },
    "& img": {
      width: GRAPH_NODE_SIDE_ICON_INNER_SIZE,
      height: GRAPH_NODE_SIDE_ICON_INNER_SIZE,
      maxWidth: "100%",
      maxHeight: "100%",
      objectFit: "contain",
      display: "block",
    },
  }
}

/** CustomNode side `IconButton` (`button` / `a`). */
export function graphNodeSideIconControlSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return graphNodeSideIconControlBaseSx(theme)
}

/** TransportNode side `a` link control. */
export function graphNodeSideIconLinkSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    ...graphNodeSideIconControlBaseSx(theme),
    textDecoration: "none",
    cursor: "pointer",
  }
}

/** React Flow handles cannot use `sx`; use inline style from the same palette. */
export function getGraphNodeHandleStyle(theme: Theme): CSSProperties {
  return {
    width: 1,
    height: 1,
    border: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.background.default,
  }
}

/** Stroke/fill for graph edges and arrow markers. */
export function getGraphEdgeColor(theme: Theme, active?: boolean): string {
  if (active) {
    return theme.palette.primary.main
  }

  return theme.palette.mode === "light"
    ? theme.palette.grey[700]
    : theme.palette.text.secondary
}
