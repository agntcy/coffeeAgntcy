/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/hooks/useTheme"

const ThemeToggleIcon: React.FC = () => {
  const { isLightMode } = useTheme()

  return isLightMode ? <Moon /> : <Sun />
}

export default ThemeToggleIcon
