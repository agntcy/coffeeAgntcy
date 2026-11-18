/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Saves light, dark, or system.
 * System, and nothing saved, follow the OS color scheme.
 * Must render inside ThemeProvider from @open-ui-kit/core.
 */

import { type ReactNode, useEffect, useMemo, useRef, useState } from "react"

import { ThemePreferenceContext } from "@/contexts/themePreference"
import { useAppThemeMode, ThemeMode } from "@/hooks/useAppThemeMode"
import {
  readOsColorScheme,
  readStoredThemeMode,
  subscribeToOsColorScheme,
  writeStoredThemeMode,
  type ResolvedColorScheme,
  type StoredThemeMode,
} from "@/utils/themeStorage"

function toThemeMode(scheme: ResolvedColorScheme): ThemeMode {
  return scheme === "dark" ? ThemeMode.Dark : ThemeMode.Light
}

export function ThemeModePersistence({ children }: { children: ReactNode }) {
  const { setMode } = useAppThemeMode()
  const setModeRef = useRef(setMode)
  const [preference, setPreference] = useState<StoredThemeMode | null>(() =>
    readStoredThemeMode(),
  )

  useEffect(() => {
    setModeRef.current = setMode
  }, [setMode])

  useEffect(() => {
    if (preference === null) {
      return
    }
    writeStoredThemeMode(preference)
  }, [preference])

  useEffect(() => {
    const apply = (scheme: ResolvedColorScheme) => {
      setModeRef.current(toThemeMode(scheme))
    }

    if (preference === "light" || preference === "dark") {
      apply(preference)
      return
    }

    apply(readOsColorScheme())
    return subscribeToOsColorScheme(apply)
  }, [preference])

  const value = useMemo(() => ({ preference, setPreference }), [preference])

  return (
    <ThemePreferenceContext.Provider value={value}>
      {children}
    </ThemePreferenceContext.Provider>
  )
}
