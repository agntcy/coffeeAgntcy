/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Merges compact typography/spacing/density onto the active OUK theme.
 * Must render inside @open-ui-kit/core ThemeProvider.
 */

import { useMemo, type ReactNode } from "react"
import {
  createTheme,
  ThemeProvider as MuiThemeProvider,
  useTheme,
} from "@mui/material/styles"

import { compactThemeOptions } from "./compactThemeOptions"

export function CompactTheme({ children }: { children: ReactNode }) {
  const oukTheme = useTheme()
  const theme = useMemo(
    () => createTheme(oukTheme, compactThemeOptions),
    [oukTheme],
  )

  return <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
}
