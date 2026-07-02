/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useAppThemeMode } from "@/hooks/useAppThemeMode"

export interface ThemeIconMap {
  light: string
  dark: string
}

/**
 * @param iconMap
 * @returns
 */
export const useThemeIcon = (iconMap: ThemeIconMap): string => {
  const { isDarkMode } = useAppThemeMode()
  return isDarkMode ? iconMap.dark : iconMap.light
}
