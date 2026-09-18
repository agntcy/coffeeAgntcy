/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Box } from "@open-ui-kit/core"
import type { SxProps, Theme } from "@mui/material/styles"
import {
  assetPngIconBareSx,
  assetPngIconMonochromeDarkFilterSx,
} from "@/utils/assetPngIcon"

export interface AssetPngIconProps {
  src: string
  alt: string
  /**
   * When true, applies `brightness(0) invert(1)` in dark mode for monochrome PNGs.
   * Do not use with theme-swapped or full-color assets.
   */
  invertInDarkMode?: boolean
  sx?: SxProps<Theme>
}

/**
 * Required wrapper for PNG/SVG images imported from `src/assets/`.
 * Sizes icons to match default MUI `SvgIcon` (`fontSize="medium"`, 24px).
 * Use inside a chip/button that already supplies border and background.
 */
export function AssetPngIcon({
  src,
  alt,
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

  return (
    <Box
      component="img"
      src={src}
      alt={alt}
      sx={assetPngIconBareSx(...sxLayers)}
    />
  )
}
