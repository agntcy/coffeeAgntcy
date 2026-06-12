/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Ghost IconButtons for graph canvas chrome (zoom/fit/lock, documentation).
 * Separate from node side icon chips — no fill at rest or on interaction.
 * Interactive states recolor glyphs via CSS filter (no outline / background).
 */

import type { Theme } from "@mui/material/styles"
import type { SystemStyleObject } from "@mui/system"
import { getAssetPngIconSize } from "@/utils/assetPngIcon"
import { getControlIconColor } from "./graphNodeSurface"

/**
 * Recolor single-color SvgIcons via filter. Each chain starts with `brightness(0)` so
 * resting `controlIconDefault` fill (light or dark grey) normalizes to black first.
 *
 * Targets (OUK `zt` primary scale):
 * - Light hover/focus → `#187adc` (zt 300 / primary.main)
 * - Light active      → `#0063c2` (zt 400 / primary.dark)
 * - Dark hover/focus  → `#79b9ff` (zt 200 — brighter on dark canvas)
 * - Dark active       → `#187adc` (zt 300)
 */
const GRAPH_CANVAS_ICON_FILTERS = {
  light: {
    hover:
      "brightness(0) saturate(100%) invert(37%) sepia(93%) saturate(1352%) hue-rotate(186deg) brightness(97%) contrast(101%)",
    active:
      "brightness(0) saturate(100%) invert(25%) sepia(98%) saturate(2476%) hue-rotate(196deg) brightness(92%) contrast(101%)",
  },
  dark: {
    hover:
      "brightness(0) saturate(100%) invert(72%) sepia(44%) saturate(749%) hue-rotate(183deg) brightness(103%) contrast(101%)",
    active:
      "brightness(0) saturate(100%) invert(37%) sepia(93%) saturate(1352%) hue-rotate(186deg) brightness(97%) contrast(101%)",
  },
} as const

function getCanvasIconFilters(theme: Theme) {
  return theme.palette.mode === "dark"
    ? GRAPH_CANVAS_ICON_FILTERS.dark
    : GRAPH_CANVAS_ICON_FILTERS.light
}

function canvasIconRestingGlyphSx(theme: Theme): SystemStyleObject<Theme> {
  const restingIconColor = getControlIconColor(theme)

  return {
    color: restingIconColor,
    "& .MuiSvgIcon-root": {
      color: restingIconColor,
      fill: restingIconColor,
    },
    "& .MuiSvgIcon-root path, & .MuiSvgIcon-root svg": {
      fill: restingIconColor,
    },
  }
}

function canvasIconFilterSx(filter: string): SystemStyleObject<Theme> {
  return {
    "& .MuiSvgIcon-root": {
      filter,
    },
  }
}

/** Zoom/fit/lock controls and the documentation floating button. */
export function graphCanvasIconButtonSx(theme: Theme): SystemStyleObject<Theme> {
  const iconButtonSize = theme.spacing(3)
  const iconSize = getAssetPngIconSize(theme)
  const iconFilters = getCanvasIconFilters(theme)
  const iconFilterTransition = theme.transitions.create(["filter"], {
    duration: theme.transitions.duration.shortest,
    easing: theme.transitions.easing.easeInOut,
  })

  return {
    width: iconButtonSize,
    height: iconButtonSize,
    minWidth: iconButtonSize,
    padding: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    border: "none",
    boxShadow: "none",
    outline: "none",
    bgcolor: "transparent",
    backgroundColor: "transparent",
    ...canvasIconRestingGlyphSx(theme),
    "& .MuiSvgIcon-root": {
      fontSize: iconSize,
      filter: "none",
      transition: iconFilterTransition,
    },
    "&:hover": {
      bgcolor: "transparent",
      backgroundColor: "transparent",
      boxShadow: "none",
      ...canvasIconFilterSx(iconFilters.hover),
      "@media (hover: none)": {
        ...canvasIconFilterSx("none"),
      },
    },
    "&:active": {
      bgcolor: "transparent",
      backgroundColor: "transparent",
      ...canvasIconFilterSx(iconFilters.active),
    },
    "&.Mui-focusVisible": {
      bgcolor: "transparent",
      backgroundColor: "transparent",
      ...canvasIconFilterSx(iconFilters.hover),
    },
    "&.Mui-disabled": {
      bgcolor: "transparent",
      backgroundColor: "transparent",
      opacity: 0.45,
      ...canvasIconFilterSx("none"),
    },
  }
}
