/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/hooks/useTheme"

interface ThemeToggleIconProps {
  className?: string
}

const ThemeToggleIcon: React.FC<ThemeToggleIconProps> = ({ className }) => {
  const { isLightMode } = useTheme()

  return isLightMode ? (
    <Moon className={className} />
  ) : (
    <Sun className={className} />
  )
}

export default ThemeToggleIcon
