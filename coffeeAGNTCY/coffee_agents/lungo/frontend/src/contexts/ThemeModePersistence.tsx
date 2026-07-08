/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Loads and saves light/dark mode via localStorage.
 * Must render inside ThemeProvider from @open-ui-kit/core.
 */

import { type ReactNode, useEffect, useLayoutEffect } from "react"

import { useAppThemeMode, ThemeMode } from "@/hooks/useAppThemeMode"
import { readStoredThemeMode, writeStoredThemeMode } from "@/utils/themeStorage"

export function ThemeModePersistence({ children }: { children: ReactNode }) {
  const { mode, setIsDarkMode } = useAppThemeMode()

  useLayoutEffect(() => {
    const storedMode = readStoredThemeMode()
    if (storedMode !== null) {
      setIsDarkMode(storedMode === "dark")
    }
  }, [setIsDarkMode])

  useEffect(() => {
    if (mode === ThemeMode.Dark) {
      writeStoredThemeMode("dark")
    } else if (mode === ThemeMode.Light) {
      writeStoredThemeMode("light")
    }
  }, [mode])

  return children
}
