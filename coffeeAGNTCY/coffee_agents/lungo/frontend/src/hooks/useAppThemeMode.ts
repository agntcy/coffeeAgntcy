/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * App helpers for OUK 2.x theme mode (ThemeMode enum + setMode API).
 */

import { ThemeMode, useThemeMode } from "@open-ui-kit/core"

export function useAppThemeMode() {
  const { mode, setMode, setTheme } = useThemeMode()
  const isDarkMode = mode === ThemeMode.Dark

  return {
    mode,
    isDarkMode,
    setMode,
    setTheme,
    setIsDarkMode: (dark: boolean) =>
      setMode(dark ? ThemeMode.Dark : ThemeMode.Light),
    toggleTheme: () => setMode(isDarkMode ? ThemeMode.Light : ThemeMode.Dark),
  }
}

export { ThemeMode }
