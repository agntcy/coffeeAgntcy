/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Persists light, dark, or system.
 * System, and a missing value, follow the OS color scheme.
 */

export const THEME_MODE_STORAGE_KEY = "lungo-theme-mode"
const DARK_COLOR_SCHEME_QUERY = "(prefers-color-scheme: dark)"

export type StoredThemeMode = "light" | "dark" | "system"
export type ResolvedColorScheme = "light" | "dark"

function isStoredThemeMode(value: string | null): value is StoredThemeMode {
  return value === "light" || value === "dark" || value === "system"
}

function matchMediaAvailable(): boolean {
  return (
    typeof window !== "undefined" && typeof window.matchMedia === "function"
  )
}

/** Dark when the browser cannot report a color scheme. */
export function readOsColorScheme(): ResolvedColorScheme {
  if (!matchMediaAvailable()) {
    return "dark"
  }
  return window.matchMedia(DARK_COLOR_SCHEME_QUERY).matches ? "dark" : "light"
}

export function subscribeToOsColorScheme(
  onChange: (scheme: ResolvedColorScheme) => void,
): () => void {
  if (!matchMediaAvailable()) {
    return () => {}
  }

  const mediaQuery = window.matchMedia(DARK_COLOR_SCHEME_QUERY)
  const handleChange = (event: MediaQueryListEvent) => {
    onChange(event.matches ? "dark" : "light")
  }
  mediaQuery.addEventListener("change", handleChange)
  return () => mediaQuery.removeEventListener("change", handleChange)
}

export function readStoredThemeMode(): StoredThemeMode | null {
  try {
    const value = localStorage.getItem(THEME_MODE_STORAGE_KEY)
    if (isStoredThemeMode(value)) {
      return value
    }
    return null
  } catch {
    return null
  }
}

/** `system` and a missing choice follow the OS color scheme. */
export function resolveStoredColorScheme(
  preference: StoredThemeMode | null,
): ResolvedColorScheme {
  if (preference === "light" || preference === "dark") {
    return preference
  }
  return readOsColorScheme()
}

export function writeStoredThemeMode(mode: StoredThemeMode): void {
  try {
    localStorage.setItem(THEME_MODE_STORAGE_KEY, mode)
  } catch {
    // Ignore quota and private browsing errors.
  }
}
