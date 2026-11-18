/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { CSSProperties } from "react"
import type { Theme } from "@mui/material/styles"
import { alpha } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import {
  getAssetPngIconBackground,
  getAssetPngIconSize,
  getGraphIconChipHoverBackground,
} from "@/utils/assetPngIcon"
import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

export interface GraphNodeSurfaceFlags {
  active?: boolean
  selected?: boolean
}

export function getControlIconColor(theme: Theme): string {
  return theme.palette.vars.controlIconDefault
}

export function getControlIconDisabledColor(theme: Theme): string {
  return theme.palette.vars.controlIconMedium
}

export interface GraphNodeRootSurfaceOptions {
  borderRadius?: string | number
}

function defaultCardRadius(theme: Theme): string | number {
  return theme.shape.borderRadius
}

function getGraphNodeRestingBackground(theme: Theme): string {
  return theme.palette.action.selected
}

export function getGraphNodeHoverBackground(theme: Theme): string {
  if (theme.palette.mode === "dark") {
    return theme.palette.vars.controlBackgroundMedium
  }

  return theme.palette.vars.baseBackgroundHover
}

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
    transition: theme.transitions.create(["background-color", "box-shadow"], {
      duration: theme.transitions.duration.shortest,
    }),
    "&:hover": {
      bgcolor: hoverBg,
      boxShadow: selected ? theme.shadows[6] : theme.shadows[2],
      outline: selected ? selectionOutline : active ? activeOutline : "none",
      borderColor: selected
        ? alpha(primary, 0.55)
        : active
          ? alpha(primary, 0.45)
          : dividerBorder,
    },
  }
}

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
      backgroundColor: hoverBg,
      "@media (hover: none)": {
        bgcolor: restingBg,
        backgroundColor: restingBg,
      },
    },
  }
}

export const GRAPH_NODE_SIDE_ICON_SIZE = "1.6rem"
const GRAPH_NODE_SIDE_ICON_INNER_SIZE = "1.125rem"

function graphNodeSideIconDarkModeGlyphSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  if (theme.palette.mode !== "dark") {
    return {}
  }

  const white = theme.palette.common.white

  return {
    ...iconGlyphFillSx(white, { important: true }),
    "&, &:hover, &:focus, &:visited, &:active": {
      color: white,
    },
  }
}

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

export function graphNodeSideIconControlSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    ...graphNodeSideIconControlBaseSx(theme),
    ...graphNodeSideIconDarkModeGlyphSx(theme),
  }
}

export function graphNodeDirectoryIconControlSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    ...graphNodeSideIconControlBaseSx(theme),
    ...graphNodeSideIconDarkModeGlyphSx(theme),
    borderRadius: "50%",
  }
}

export function getGraphNodeHandleStyle(theme: Theme): CSSProperties {
  return {
    width: 1,
    height: 1,
    border: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.action.selected,
  }
}

export function getGraphEdgeColor(theme: Theme, active?: boolean): string {
  if (active) {
    return theme.palette.primary.main
  }

  return theme.palette.mode === "light"
    ? theme.palette.grey[700]
    : theme.palette.text.secondary
}
