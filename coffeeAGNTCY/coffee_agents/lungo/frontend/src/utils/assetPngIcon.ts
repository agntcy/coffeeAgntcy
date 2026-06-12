/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { SxProps, Theme } from "@mui/material/styles"

/**
 * MUI `SvgIcon` default size (`fontSize="medium"`) — `theme.typography.pxToRem(24)`.
 * @see node_modules/@mui/material/esm/SvgIcon/SvgIcon.js
 */
export const ASSET_PNG_ICON_SIZE_PX = 24

/** Resolved width/height for asset PNGs (matches default MUI icon `fontSize="medium"`). */
export function getAssetPngIconSize(theme: Theme): string {
  return theme.typography.pxToRem(ASSET_PNG_ICON_SIZE_PX)
}

/** Theme-aware fill behind PNG icons (white in light mode, dark grey in dark mode). */
export function getAssetPngIconBackground(theme: Theme): string {
  return theme.palette.mode === "light"
    ? theme.palette.common.white
    : theme.palette.grey[800]
}

/** Slightly tinted chip background on hover (graph icon buttons/links). */
export function getGraphIconChipHoverBackground(theme: Theme): string {
  return theme.palette.mode === "light"
    ? theme.palette.grey[100]
    : theme.palette.grey[700]
}

/**
 * Inverts monochrome PNG artwork to white in dark mode (`brightness(0) invert(1)`).
 * For dark glyphs on transparent backgrounds — not for full-color or theme-swapped PNGs.
 */
export function assetPngIconMonochromeDarkFilterSx(): SxProps<Theme> {
  return (theme: Theme) =>
    theme.palette.mode === "dark" ? { filter: "brightness(0) invert(1)" } : {}
}

/** Size-only `sx` for PNGs nested inside a chip/button that already supplies border/background. */
export function assetPngIconBareSx(...extra: SxProps<Theme>[]): SxProps<Theme> {
  return [
    (theme: Theme) => ({
      width: getAssetPngIconSize(theme),
      height: getAssetPngIconSize(theme),
      objectFit: "contain",
      display: "block",
      flexShrink: 0,
    }),
    ...extra,
  ] as SxProps<Theme>
}

/** Full chip `sx` for PNG icons from `src/assets/` — always use via {@link AssetPngIcon}. */
export function assetPngIconChipSx(...extra: SxProps<Theme>[]): SxProps<Theme> {
  return [
    (theme: Theme) => ({
      width: getAssetPngIconSize(theme),
      height: getAssetPngIconSize(theme),
      bgcolor: getAssetPngIconBackground(theme),
      border: "1px solid",
      borderColor: theme.palette.divider,
      borderRadius: theme.shape.borderRadius,
      objectFit: "contain",
      display: "block",
      flexShrink: 0,
      boxSizing: "border-box",
    }),
    ...extra,
  ] as SxProps<Theme>
}
