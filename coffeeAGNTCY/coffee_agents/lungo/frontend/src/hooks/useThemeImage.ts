/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useThemeMode } from "@open-ui-kit/core"

interface ThemeImageMap {
  light: string
  dark: string
}

export const useThemeImage = (imageMap: ThemeImageMap): string => {
  const { isDarkMode } = useThemeMode()

  return isDarkMode ? imageMap.dark : imageMap.light
}
