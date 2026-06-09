/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Persisted light/dark theme preference in localStorage.
 */

export const THEME_MODE_STORAGE_KEY = "lungo-theme-mode"

export type StoredThemeMode = "light" | "dark"

export function readStoredThemeMode(): StoredThemeMode | null {
  try {
    const value = localStorage.getItem(THEME_MODE_STORAGE_KEY)
    if (value === "light" || value === "dark") {
      return value
    }
    return null
  } catch {
    return null
  }
}

export function readStoredIsDarkMode(): boolean | null {
  const mode = readStoredThemeMode()
  if (mode === null) return null
  return mode === "dark"
}

export function writeStoredThemeMode(mode: StoredThemeMode): void {
  try {
    localStorage.setItem(THEME_MODE_STORAGE_KEY, mode)
  } catch {
    // Ignore quota / private browsing errors.
  }
}
