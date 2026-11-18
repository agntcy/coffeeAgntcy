/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import useMediaQuery from "@mui/material/useMediaQuery"
import { useTheme } from "@mui/material/styles"

export function useIsBelowSmBreakpoint(): boolean {
  const theme = useTheme()
  return useMediaQuery(theme.breakpoints.down("sm"))
}
