/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Persisted light/dark theme preference in localStorage.
 */

export const THEME_MODE_STORAGE_KEY = "corto-theme-mode"
const LEGACY_THEME_STORAGE_KEY = "theme"

export type StoredThemeMode = "light" | "dark"

function resolveLegacyThemeMode(): StoredThemeMode | null {
  const legacy = localStorage.getItem(LEGACY_THEME_STORAGE_KEY)
  if (legacy === "light" || legacy === "dark") {
    return legacy
  }
  if (legacy === "system") {
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light"
  }
  return null
}

export function readStoredThemeMode(): StoredThemeMode | null {
  try {
    const value = localStorage.getItem(THEME_MODE_STORAGE_KEY)
    if (value === "light" || value === "dark") {
      return value
    }

    const migrated = resolveLegacyThemeMode()
    if (migrated !== null) {
      localStorage.setItem(THEME_MODE_STORAGE_KEY, migrated)
      localStorage.removeItem(LEGACY_THEME_STORAGE_KEY)
    }
    return migrated
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
