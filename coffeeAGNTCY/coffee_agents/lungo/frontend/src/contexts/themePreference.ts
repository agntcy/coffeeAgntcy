/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Stored theme preference, separate from the resolved Open UI Kit mode.
 */

import { createContext } from "react"

import type { StoredThemeMode } from "@/utils/themeStorage"

export interface ThemePreferenceContextValue {
  preference: StoredThemeMode | null
  setPreference: (mode: StoredThemeMode) => void
}

export const ThemePreferenceContext =
  createContext<ThemePreferenceContextValue | null>(null)
