/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { createContext } from "react"

export type Theme = "light" | "dark" | "system"

export interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  isLightMode: boolean
  resolvedTheme: "light" | "dark"
}

export const ThemeContext = createContext<ThemeContextType | undefined>(
  undefined,
)
