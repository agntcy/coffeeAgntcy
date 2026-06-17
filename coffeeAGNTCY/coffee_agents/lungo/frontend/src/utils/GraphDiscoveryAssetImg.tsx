/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { AssetPngIcon } from "@/components/AssetPngIcon"

export function GraphDiscoveryAssetImg({
  src,
  alt,
  invertInDarkMode = false,
}: {
  src: string
  alt: string
  invertInDarkMode?: boolean
}) {
  return (
    <AssetPngIcon
      bare
      src={src}
      alt={alt}
      invertInDarkMode={invertInDarkMode}
    />
  )
}
