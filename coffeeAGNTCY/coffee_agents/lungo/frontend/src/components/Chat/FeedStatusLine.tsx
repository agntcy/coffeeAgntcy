/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { ReactNode } from "react"
import { Typography } from "@open-ui-kit/core"
import { LoadingDots } from "@/components/loading"

export interface FeedStatusLineProps {
  children: ReactNode
  showDots?: boolean
}

export function FeedStatusLine({
  children,
  showDots = false,
}: FeedStatusLineProps) {
  return (
    <Typography
      variant="body1"
      component="div"
      sx={{
        whiteSpace: "pre-wrap",
        overflowWrap: "break-word",
        wordBreak: "break-word",
        py: 1,
        px: 1,
      }}
    >
      {children}
      {showDots ? <LoadingDots /> : null}
    </Typography>
  )
}
