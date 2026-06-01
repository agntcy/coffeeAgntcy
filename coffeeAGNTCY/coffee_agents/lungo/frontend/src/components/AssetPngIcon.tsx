/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Box } from "@open-ui-kit/core"
import type { SxProps, Theme } from "@mui/material/styles"
import {
  assetPngIconBareSx,
  assetPngIconChipSx,
  assetPngIconMonochromeDarkFilterSx,
} from "@/utils/assetPngIcon"

export interface AssetPngIconProps {
  src: string
  alt: string
  /** When true, only size/object-fit — for use inside {@link graphSideIconButtonSx} chips. */
  bare?: boolean
  /**
   * When true, applies `brightness(0) invert(1)` in dark mode for monochrome PNGs.
   * Do not use with theme-swapped or full-color assets.
   */
  invertInDarkMode?: boolean
  sx?: SxProps<Theme>
}

/**
 * Required wrapper for PNG images imported from `src/assets/`.
 * Sizes icons to match default MUI `SvgIcon` (`fontSize="medium"`, 24px) and applies
 * theme-aware background, border, and radius (same as graph MUI/SVG icon chips).
 */
export function AssetPngIcon({
  src,
  alt,
  bare = false,
  invertInDarkMode = false,
  sx,
}: AssetPngIconProps) {
  const sxLayers: SxProps<Theme>[] = []
  if (invertInDarkMode) {
    sxLayers.push(assetPngIconMonochromeDarkFilterSx())
  }
  if (sx) {
    sxLayers.push(sx)
  }

  const resolvedSx = bare
    ? assetPngIconBareSx(...sxLayers)
    : assetPngIconChipSx(...sxLayers)

  return <Box component="img" src={src} alt={alt} sx={resolvedSx} />
}
