/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * App helpers for OUK 2.x theme mode (ThemeMode enum + setMode API).
 */

import { useCallback } from "react"
import { useThemeMode, ThemeMode } from "@open-ui-kit/core"

export function useAppThemeMode() {
  const { mode, setMode, setTheme } = useThemeMode()
  const isDarkMode = mode === ThemeMode.Dark

  const setIsDarkMode = useCallback(
    (dark: boolean) => setMode(dark ? ThemeMode.Dark : ThemeMode.Light),
    [setMode],
  )

  const toggleTheme = useCallback(
    () => setMode(isDarkMode ? ThemeMode.Light : ThemeMode.Dark),
    [setMode, isDarkMode],
  )

  return {
    mode,
    isDarkMode,
    setMode,
    setTheme,
    setIsDarkMode,
    toggleTheme,
  }
}

export { ThemeMode }
