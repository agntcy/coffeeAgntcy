/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Open UI Kit theme provider. Saved choices are light, dark, or system.
 * System, and nothing saved, follow the OS color scheme.
 */

import { type ReactNode } from "react"
import { ThemeProvider as OpenUiKitThemeProvider } from "@open-ui-kit/core"

import { CompactTheme } from "@/contexts/CompactTheme"
import { ThemeModePersistence } from "@/contexts/ThemeModePersistence"
import { ThemeMode } from "@/hooks/useApp"
import {
  readStoredThemeMode,
  resolveStoredColorScheme,
} from "@/utils/themeStorage"

export function OpenUiKitThemeBridge({ children }: { children: ReactNode }) {
  const defaultScheme = resolveStoredColorScheme(readStoredThemeMode())
  const defaultMode =
    defaultScheme === "dark" ? ThemeMode.Dark : ThemeMode.Light

  return (
    <OpenUiKitThemeProvider defaultMode={defaultMode}>
      <CompactTheme>
        <ThemeModePersistence>{children}</ThemeModePersistence>
      </CompactTheme>
    </OpenUiKitThemeProvider>
  )
}
