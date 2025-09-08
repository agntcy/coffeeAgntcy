/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useTheme } from "@/hooks/useTheme"

export interface ThemeIconMap {
  light: string
  dark: string
}

/**
 * @param iconMap
 * @returns
 */
export const useThemeIcon = (iconMap: ThemeIconMap): string => {
  const { resolvedTheme } = useTheme()
  return resolvedTheme === "light" ? iconMap.light : iconMap.dark
}

/**
 * @param lightClass
 * @param darkClass
 * @returns
 */
export const useThemeClass = (
  lightClass: string,
  darkClass: string,
): string => {
  const { resolvedTheme } = useTheme()
  return resolvedTheme === "light" ? lightClass : darkClass
}
