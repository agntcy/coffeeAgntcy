/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * True when the viewport width is strictly below the layout `sm` breakpoint (600px).
 */

import useMediaQuery from "@mui/material/useMediaQuery"
import { useTheme } from "@mui/material/styles"

export function useIsBelowSmBreakpoint(): boolean {
  const theme = useTheme()
  return useMediaQuery(theme.breakpoints.down("sm"))
}
