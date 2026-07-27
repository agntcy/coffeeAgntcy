/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import githubIconDark from "@/assets/Github.png"
import githubIconLight from "@/assets/Github_lightmode.png"
import { useThemeIcon } from "./useThemeIcon"

const githubIconMap = {
  light: githubIconLight,
  dark: githubIconDark,
} as const

/** Theme-aware GitHub icon URL for `<img src={...} />` usage. */
export const useGithubIcon = (): string => useThemeIcon(githubIconMap)
