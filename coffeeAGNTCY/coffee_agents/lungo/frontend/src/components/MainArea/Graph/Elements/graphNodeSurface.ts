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

/** Workflow highlight (`data.active`) and chat selection (`data.selected`) are independent. */
export interface GraphNodeSurfaceFlags {
  active?: boolean
  selected?: boolean
}

/** OUK control icon fill (`#e8e9ea` in dark mode) — not `brandIconPrimaryDefault`. */
export function getControlIconColor(theme: Theme): string {
  return theme.palette.vars.controlIconDefault
}

export interface GraphNodeRootSurfaceOptions {
  /** Defaults to theme.shape.borderRadius (typically 4px). */
  borderRadius?: string | number
}

function defaultCardRadius(theme: Theme): string | number {
  return theme.shape.borderRadius
}

function getGraphNodeRestingBackground(theme: Theme): string {
  return theme.palette.action.selected
}

/** Hover background for every graph node surface (CustomNode, TransportNode, …). */
export function getGraphNodeHoverBackground(theme: Theme): string {
  if (theme.palette.mode === "dark") {
    return theme.palette.vars.controlBackgroundMedium
  }

  return theme.palette.vars.baseBackgroundHover
}

/**
 * Root node surface: palette-driven border/background, hover lift, and focus ring.
 * Merge with layout-only `sx` (width, flexDirection, etc.) in each node component.
 */
export function graphNodeRootSurfaceSx(
  theme: Theme,
  flags: GraphNodeSurfaceFlags = {},
  options: GraphNodeRootSurfaceOptions = {},
): SystemStyleObject<Theme> {
  const { active = false, selected = false } = flags
  const borderRadius = options.borderRadius ?? defaultCardRadius(theme)
  const dividerBorder = theme.palette.divider
  const primary = theme.palette.primary.main
  const restingBg = getGraphNodeRestingBackground(theme)
  const hoverBg = getGraphNodeHoverBackground(theme)

  const selectionOutline = `2px solid ${primary}`
  const activeOutline = `2px solid ${alpha(primary, 0.45)}`

  const restingOutline = selected
    ? selectionOutline
    : active
      ? activeOutline
      : "none"

  const restingShadow = selected || active ? theme.shadows[4] : "none"
  const restingBorderColor = selected
    ? alpha(primary, 0.55)
    : active
      ? alpha(primary, 0.45)
      : dividerBorder

  return {
    border: "1px solid",
    borderColor: restingBorderColor,
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
      boxShadow: selected ? theme.shadows[6] : theme.shadows[2],
      // Selection ring is persistent; hover only lifts unselected nodes subtly.
      outline: selected ? selectionOutline : active ? activeOutline : "none",
      borderColor: selected
        ? alpha(primary, 0.55)
        : active
          ? alpha(primary, 0.45)
          : dividerBorder,
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
    backgroundColor: theme.palette.action.selected,
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
