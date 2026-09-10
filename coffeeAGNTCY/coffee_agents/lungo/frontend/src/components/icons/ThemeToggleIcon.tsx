/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Icons } from "@open-ui-kit/core"
import { useAppThemeMode } from "@/hooks/useApp"

const ThemeToggleIcon: React.FC = () => {
  const { isDarkMode } = useAppThemeMode()

  // Moon when app is light (switch to dark); sun when app is dark (switch to light).
  return isDarkMode ? <Icons.LightMode /> : <Icons.DarkMode />
}

export default ThemeToggleIcon
