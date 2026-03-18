/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Syncs Open UI Kit (MUI) theme with Lungo ThemeContext.
 * Render only inside ThemeProvider from @/contexts/ThemeContext.
 **/

import type { ReactNode } from "react"
import { ThemeProvider as OpenUiKitThemeProvider } from "@open-ui-kit/core"
import { useTheme } from "@/hooks/useTheme"

export function OpenUiKitThemeBridge({ children }: { children: ReactNode }) {
  const { isLightMode } = useTheme()
  return (
    <OpenUiKitThemeProvider isDarkMode={!isLightMode}>
      {children}
    </OpenUiKitThemeProvider>
  )
}
