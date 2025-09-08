/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useTheme } from "@/hooks/useTheme"

interface ThemeImageMap {
  light: string
  dark: string
}

export const useThemeImage = (imageMap: ThemeImageMap): string => {
  const { resolvedTheme } = useTheme()

  return resolvedTheme === "light" ? imageMap.light : imageMap.dark
}
