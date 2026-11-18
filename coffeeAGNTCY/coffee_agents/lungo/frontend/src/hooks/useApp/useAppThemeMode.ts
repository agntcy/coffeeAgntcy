/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * App helpers for OUK 2.x theme mode (ThemeMode enum + setMode API).
 */

import { useCallback, useContext } from "react"
import { useThemeMode, ThemeMode } from "@open-ui-kit/core"

import { ThemePreferenceContext } from "@/contexts/themePreference"
import type { StoredThemeMode } from "@/utils/themeStorage"

export function useAppThemeMode() {
  const { mode, setMode, setTheme } = useThemeMode()
  const preferenceApi = useContext(ThemePreferenceContext)
  const isDarkMode = mode === ThemeMode.Dark

  const setIsDarkMode = useCallback(
    (dark: boolean) => {
      const next = dark ? "dark" : "light"
      if (preferenceApi) {
        preferenceApi.setPreference(next)
        return
      }
      setMode(dark ? ThemeMode.Dark : ThemeMode.Light)
    },
    [preferenceApi, setMode],
  )

  const toggleTheme = useCallback(() => {
    const next = isDarkMode ? "light" : "dark"
    if (preferenceApi) {
      preferenceApi.setPreference(next)
      return
    }
    setMode(isDarkMode ? ThemeMode.Light : ThemeMode.Dark)
  }, [preferenceApi, setMode, isDarkMode])

  const setThemePreference = useCallback(
    (next: StoredThemeMode) => {
      if (preferenceApi) {
        preferenceApi.setPreference(next)
        return
      }
      if (next === "light" || next === "dark") {
        setMode(next === "dark" ? ThemeMode.Dark : ThemeMode.Light)
      }
    },
    [preferenceApi, setMode],
  )

  return {
    mode,
    isDarkMode,
    preference: preferenceApi?.preference ?? null,
    setMode,
    setTheme,
    setIsDarkMode,
    setThemePreference,
    toggleTheme,
  }
}

export { ThemeMode }
