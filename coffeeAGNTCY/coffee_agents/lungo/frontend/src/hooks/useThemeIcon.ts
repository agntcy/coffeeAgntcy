/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useThemeMode } from "@open-ui-kit/core"

export interface ThemeIconMap {
  light: string
  dark: string
}

/**
 * @param iconMap
 * @returns
 */
export const useThemeIcon = (iconMap: ThemeIconMap): string => {
  const { isDarkMode } = useThemeMode()
  return isDarkMode ? iconMap.dark : iconMap.light
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
  const { isDarkMode } = useThemeMode()
  return isDarkMode ? darkClass : lightClass
}
