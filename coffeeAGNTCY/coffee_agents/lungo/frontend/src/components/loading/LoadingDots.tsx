/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { keyframes } from "@emotion/react"
import { Box, Stack } from "@open-ui-kit/core"

/** Keep dim phase well above ~0.35 so dots stay visible on light and dark surfaces. */
const dotPulse = keyframes`
  0%, 80%, 100% { opacity: 0.58; }
  40% { opacity: 1; }
`

export interface LoadingDotsProps {
  size?: number
  color?: "text.primary" | "text.secondary" | "inherit"
}

export function LoadingDots({
  size = 14,
  color = "text.primary",
}: LoadingDotsProps) {
  return (
    <Stack
      component="span"
      direction="row"
      spacing={0.25}
      aria-hidden
      sx={{ display: "inline-flex", alignItems: "center", ml: 0.5 }}
    >
      {[0, 1, 2].map((i) => (
        <Box
          key={`dot-${i}`}
          component="span"
          sx={(theme) => ({
            fontSize: size,
            lineHeight: 1,
            color:
              color === "inherit"
                ? "inherit"
                : color === "text.secondary"
                  ? theme.palette.text.secondary
                  : theme.palette.text.primary,
            animation: `${dotPulse} 1.2s infinite`,
            animationDelay: `${i * 0.15}s`,
          })}
        >
          .
        </Box>
      ))}
    </Stack>
  )
}
