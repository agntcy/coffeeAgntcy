/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import Box from "@mui/material/Box"

export function GraphDiscoveryAssetImg({
  src,
  alt,
}: {
  src: string
  alt: string
}) {
  return (
    <Box
      component="img"
      src={src}
      alt={alt}
      sx={{
        objectFit: "contain",
        opacity: 1,
        bgcolor: "#ffffff",
      }}
    />
  )
}
