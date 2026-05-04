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

/** Small square behind the node glyph (CustomNode icon row). */
export function graphNodeIconSlotSx(theme: Theme): SystemStyleObject<Theme> {
  return {
    bgcolor:
      theme.palette.mode === "light"
        ? theme.palette.grey[100]
        : theme.palette.grey[800],
    borderRadius: 1,
  }
}

/** GitHub / similar auxiliary control: paper surface + divider frame + opacity hover. */
export function graphNodeAuxiliaryControlSurfaceSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    borderRadius: 1,
    border: "1px solid",
    borderColor: theme.palette.divider,
    bgcolor: theme.palette.background.paper,
    boxShadow: theme.shadows[1],
    opacity: 1,
    transition: theme.transitions.create("opacity", {
      duration: theme.transitions.duration.shortest,
      easing: theme.transitions.easing.easeInOut,
    }),
    "&:hover": { opacity: 0.8 },
  }
}

/** IconButton stack on the side of CustomNode — size + shadow + hover opacity. */
export function graphNodeSideIconButtonSx(
  theme: Theme,
): SystemStyleObject<Theme> {
  return {
    width: 28,
    height: 28,
    boxShadow: theme.shadows[1],
    "&:hover": { opacity: 0.8 },
  }
}

export function graphNodeSideIconButtonSxWithModal(
  theme: Theme,
  isModalOpen: boolean,
): SystemStyleObject<Theme> {
  return {
    width: 28,
    height: 28,
    boxShadow: theme.shadows[1],
    "&:hover": { opacity: isModalOpen ? 1 : 0.8 },
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
