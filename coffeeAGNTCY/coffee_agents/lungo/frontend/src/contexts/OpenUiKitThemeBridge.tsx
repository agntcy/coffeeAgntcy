/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Open UI Kit theme provider with persisted light/dark mode.
 **/

import { type ReactNode } from "react"
import { ThemeProvider as OpenUiKitThemeProvider } from "@open-ui-kit/core"

import { ThemeModePersistence } from "@/contexts/ThemeModePersistence"
import { readStoredIsDarkMode } from "@/utils/themeStorage"

export function OpenUiKitThemeBridge({ children }: { children: ReactNode }) {
  const storedIsDarkMode = readStoredIsDarkMode()

  return (
    <OpenUiKitThemeProvider defaultDarkMode={storedIsDarkMode ?? false}>
      <ThemeModePersistence>{children}</ThemeModePersistence>
    </OpenUiKitThemeProvider>
  )
}
