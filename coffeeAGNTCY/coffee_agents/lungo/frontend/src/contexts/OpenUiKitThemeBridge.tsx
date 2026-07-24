/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Open UI Kit theme provider with persisted light/dark mode.
 **/

import { type ReactNode } from "react"
import { ThemeProvider as OpenUiKitThemeProvider } from "@open-ui-kit/core"

import { CompactTheme } from "@/contexts/CompactTheme"
import { ThemeModePersistence } from "@/contexts/ThemeModePersistence"
import { ThemeMode } from "@/hooks/useAppThemeMode"
import { readStoredIsDarkMode } from "@/utils/themeStorage"

export function OpenUiKitThemeBridge({ children }: { children: ReactNode }) {
  const storedIsDarkMode = readStoredIsDarkMode()
  const defaultMode =
    storedIsDarkMode === null
      ? ThemeMode.Light
      : storedIsDarkMode
        ? ThemeMode.Dark
        : ThemeMode.Light

  return (
    <OpenUiKitThemeProvider defaultMode={defaultMode}>
      <CompactTheme>
        <ThemeModePersistence>{children}</ThemeModePersistence>
      </CompactTheme>
    </OpenUiKitThemeProvider>
  )
}
