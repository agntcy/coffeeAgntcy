/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useMemo } from "react"
import { Spinner, SpinnerProps, Stack, Typography } from "@open-ui-kit/core"

enum SpinnerSizeCategory {
  SMALL = "small",
  MEDIUM = "medium",
  LARGE = "large",
}

enum SpinnerSize {
  SMALL = "20px",
  MEDIUM = "24px",
  LARGE = "40px",
}

export interface LoadingSpinnerProps {
  message?: string
  size?: SpinnerProps["size"] | SpinnerSizeCategory
  thickness?: number
  /** No padding; use in modals and other tight layouts */
  compact?: boolean
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message,
  size,
  thickness = 4,
  compact = false,
}) => {
  const selectedSize = useMemo(() => {
    if (!size) {
      return SpinnerSize.MEDIUM
    }

    switch (size) {
      case SpinnerSizeCategory.SMALL:
        return SpinnerSize.SMALL
      case SpinnerSizeCategory.MEDIUM:
        return SpinnerSize.MEDIUM
      case SpinnerSizeCategory.LARGE:
        return SpinnerSize.LARGE
      default:
        return size
    }
  }, [size])

  return (
    <Stack
      alignItems="center"
      justifyContent="center"
      spacing={compact ? 0 : 1}
      sx={{ p: compact ? 0 : 2 }}
    >
      <Spinner size={selectedSize} thickness={thickness} />
      {message ? (
        <Typography
          variant="caption"
          sx={{
            textAlign: "center",
            opacity: 0.6,
            maxWidth: 280,
          }}
        >
          {message}
        </Typography>
      ) : null}
    </Stack>
  )
}
