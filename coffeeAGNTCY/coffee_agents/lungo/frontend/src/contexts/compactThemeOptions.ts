/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Compact density layer merged onto the OUK theme (see CompactTheme).
 * Body scale shifts one OUK tier down (body1: 16px → 14px); spacing unit: 6px.
 */

import type { ThemeOptions } from "@mui/material/styles"

/** 6px per spacing unit (default MUI/OUK is 8px). */
export const COMPACT_SPACING_UNIT_PX = 6

type SpacingFn = ((...args: number[]) => string) & { mui: true }

/**
 * Must be a spacing factory when merging onto an existing theme — `spacing: 6`
 * deep-merges as a number and breaks `theme.spacing()` (e.g. MuiToolbar).
 */
function createCompactSpacing(unitPx: number): SpacingFn {
  const spacing = (...args: number[]) => {
    const factors = args.length === 0 ? [1] : args
    return factors.map((factor) => `${unitPx * factor}px`).join(" ")
  }
  spacing.mui = true as const
  return spacing
}

const compactSpacing = createCompactSpacing(COMPACT_SPACING_UNIT_PX)

export const compactThemeOptions: ThemeOptions = {
  spacing: compactSpacing,

  typography: {
    htmlFontSize: 16,

    body1: { fontSize: "14px", lineHeight: "20px" },
    body1Semibold: { fontSize: "14px", lineHeight: "20px" },
    body2: { fontSize: "12px", lineHeight: "16px" },
    body2Semibold: { fontSize: "12px", lineHeight: "16px" },
    subtitle1: { fontSize: "14px", lineHeight: "20px" },
    subtitle2: { fontSize: "12px", lineHeight: "16px" },
    headingSubSection: { fontSize: "14px", lineHeight: "20px" },

    caption: { fontSize: "11px", lineHeight: "15px" },
    captionMedium: { fontSize: "11px", lineHeight: "15px" },
    captionSemibold: { fontSize: "11px", lineHeight: "15px" },

    h6: { fontSize: "18px", lineHeight: "25px" },
    h5: { fontSize: "21px", lineHeight: "28px" },
    h4: { fontSize: "24px", lineHeight: "32px" },
    h3: { fontSize: "32px", lineHeight: "38px" },
    h2: { fontSize: "42px", lineHeight: "46px" },
    h1: { fontSize: "52px", lineHeight: "56px" },

    button: { fontSize: "11px", lineHeight: "15px" },
    overline: { fontSize: "9px", lineHeight: "14px" },
  },

  components: {
    MuiButton: { defaultProps: { size: "small" } },
    MuiIconButton: { defaultProps: { size: "small" } },
    MuiTextField: { defaultProps: { margin: "dense", size: "small" } },
    MuiInputBase: { defaultProps: { margin: "dense" } },
    MuiInputLabel: { defaultProps: { margin: "dense" } },
    MuiFormControl: { defaultProps: { margin: "dense" } },
    MuiFormHelperText: { defaultProps: { margin: "dense" } },
    MuiOutlinedInput: { defaultProps: { margin: "dense" } },
    MuiFilledInput: { defaultProps: { margin: "dense" } },
    MuiListItem: { defaultProps: { dense: true } },
    MuiListItemButton: { defaultProps: { dense: true } },
    MuiToolbar: { defaultProps: { variant: "dense" } },
    MuiTable: { defaultProps: { size: "small" } },
    MuiChip: { defaultProps: { size: "small" } },
    MuiFab: { defaultProps: { size: "small" } },
  },
}
