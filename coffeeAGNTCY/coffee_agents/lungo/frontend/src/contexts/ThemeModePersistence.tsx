/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Loads and saves light/dark mode via localStorage.
 * Must render inside ThemeProvider from @open-ui-kit/core.
 */

import { type ReactNode, useEffect, useLayoutEffect } from "react"
import { useThemeMode } from "@open-ui-kit/core"

import { readStoredThemeMode, writeStoredThemeMode } from "@/utils/themeStorage"

export function ThemeModePersistence({ children }: { children: ReactNode }) {
  const { isDarkMode, setIsDarkMode } = useThemeMode()

  useLayoutEffect(() => {
    const storedMode = readStoredThemeMode()
    if (storedMode !== null) {
      setIsDarkMode(storedMode === "dark")
    }
  }, [setIsDarkMode])

  useEffect(() => {
    writeStoredThemeMode(isDarkMode ? "dark" : "light")
  }, [isDarkMode])

  return children
}
