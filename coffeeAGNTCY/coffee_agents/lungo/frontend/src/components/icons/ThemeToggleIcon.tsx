/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { useAppThemeMode } from "@/hooks/useAppThemeMode"
import DarkMode from "@mui/icons-material/DarkMode"
import LightMode from "@mui/icons-material/LightMode"

const ThemeToggleIcon: React.FC = () => {
  const { isDarkMode } = useAppThemeMode()

  // Moon when app is light (switch to dark); sun when app is dark (switch to light).
  return isDarkMode ? <LightMode /> : <DarkMode />
}

export default ThemeToggleIcon
