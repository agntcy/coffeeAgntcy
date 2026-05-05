/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import DarkMode from "@mui/icons-material/DarkMode"
import LightMode from "@mui/icons-material/LightMode"
import { useTheme } from "@/hooks/useTheme"

const iconSx = {
  fontSize: 20,
} as const

const ThemeToggleIcon: React.FC = () => {
  const { isLightMode } = useTheme()

  return isLightMode ? <DarkMode sx={iconSx} /> : <LightMode sx={iconSx} />
}

export default ThemeToggleIcon
