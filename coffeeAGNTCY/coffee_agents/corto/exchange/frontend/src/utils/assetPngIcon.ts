/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { SxProps, Theme } from "@mui/material/styles"

export const ASSET_PNG_ICON_SIZE_PX = 24

export function getAssetPngIconSize(theme: Theme): string {
  return theme.typography.pxToRem(ASSET_PNG_ICON_SIZE_PX)
}

export function getAssetPngIconBackground(theme: Theme): string {
  return theme.palette.mode === "light"
    ? theme.palette.common.white
    : theme.palette.grey[800]
}

export function getGraphIconChipHoverBackground(theme: Theme): string {
  return theme.palette.mode === "light"
    ? theme.palette.grey[100]
    : theme.palette.grey[700]
}

export function assetPngIconMonochromeDarkFilterSx(): SxProps<Theme> {
  return (theme: Theme) =>
    theme.palette.mode === "dark" ? { filter: "brightness(0) invert(1)" } : {}
}

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
