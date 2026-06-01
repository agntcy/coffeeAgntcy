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

export interface GraphNodeRootSurfaceOptions {
  /** Defaults to 2× theme.shape.borderRadius (typically 8px). */
  borderRadius?: string | number
}

function defaultCardRadius(theme: Theme): string | number {
  const r = theme.shape.borderRadius
  return typeof r === "number" ? r * 2 : r
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
  const paper = theme.palette.background.paper
  const borderColor = theme.palette.divider
  const primary = theme.palette.primary.main

  const restingBg =
    state === "active"
      ? alpha(primary, theme.palette.action.selectedOpacity)
      : paper

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
      bgcolor: theme.palette.action.hover,
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
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: iconSize,
    height: iconSize,
    flexShrink: 0,
    boxSizing: "border-box",
    bgcolor: getAssetPngIconBackground(theme),
    border: "1px solid",
    borderColor: theme.palette.divider,
    borderRadius: theme.shape.borderRadius,
    "& .MuiSvgIcon-root": {
      fontSize: iconSize,
    },
  }
}

/** @deprecated Use {@link graphIconChipSx}. */
export function graphNodeIconSlotSx(theme: Theme): SystemStyleObject<Theme> {
  return graphIconChipSx(theme)
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

/** Graph IconButton chip — MUI default is 40×40 (`padding: 8` + 24px icon). */
export function graphSideIconButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  const iconButtonSize = theme.spacing(5)

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

/** @deprecated Use {@link graphSideIconButtonSx}. */
export function graphNodeSideIconButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return graphSideIconButtonSx(theme)
}

export function graphSideIconButtonSxWithModal(
  theme: Theme,
  _isModalOpen: boolean,
): SystemStyleObject<Theme> {
  return graphSideIconButtonSx(theme)
}

/** @deprecated Use {@link graphSideIconButtonSxWithModal}. */
export function graphNodeSideIconButtonSxWithModal(
  theme: Theme,
  isModalOpen: boolean,
): SystemStyleObject<Theme> {
  return graphSideIconButtonSxWithModal(theme, isModalOpen)
}

/** GitHub / similar auxiliary link control — same chip as graph IconButtons. */
export function graphNodeAuxiliaryControlSurfaceSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    ...graphSideIconButtonSx(theme),
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
