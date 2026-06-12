/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * OUK typography variants merged into the MUI theme.
 */

import type { CSSProperties } from "react"

declare module "@mui/material/styles" {
  interface TypographyVariants {
    body1Semibold: CSSProperties
    body2Semibold: CSSProperties
    headingSubSection: CSSProperties
    captionMedium: CSSProperties
    captionSemibold: CSSProperties
  }

  interface TypographyVariantsOptions {
    body1Semibold?: CSSProperties
    body2Semibold?: CSSProperties
    headingSubSection?: CSSProperties
    captionMedium?: CSSProperties
    captionSemibold?: CSSProperties
  }
}

declare module "@mui/material/Typography" {
  interface TypographyPropsVariantOverrides {
    body1Semibold: true
    body2Semibold: true
    headingSubSection: true
    captionMedium: true
    captionSemibold: true
  }
}

export {}
