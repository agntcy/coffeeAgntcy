/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Moon, Sun } from "lucide-react"
import { useThemeMode } from "@open-ui-kit/core"

const ThemeToggleIcon: React.FC = () => {
  const { isDarkMode } = useThemeMode()

  return isDarkMode ? <Sun /> : <Moon />
}

export default ThemeToggleIcon
