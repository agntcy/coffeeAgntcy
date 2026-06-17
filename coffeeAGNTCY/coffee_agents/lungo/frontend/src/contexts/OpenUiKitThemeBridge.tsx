/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Open UI Kit theme provider with persisted light/dark mode.
 **/

import { type ReactNode } from "react"
import { ThemeProvider as OpenUiKitThemeProvider } from "@open-ui-kit/core"

import { LungoCompactTheme } from "@/contexts/LungoCompactTheme"
import { ThemeModePersistence } from "@/contexts/ThemeModePersistence"
import { readStoredIsDarkMode } from "@/utils/themeStorage"

export function OpenUiKitThemeBridge({ children }: { children: ReactNode }) {
  const storedIsDarkMode = readStoredIsDarkMode()

  return (
    <OpenUiKitThemeProvider defaultDarkMode={storedIsDarkMode ?? false}>
      <LungoCompactTheme>
        <ThemeModePersistence>{children}</ThemeModePersistence>
      </LungoCompactTheme>
    </OpenUiKitThemeProvider>
  )
}
