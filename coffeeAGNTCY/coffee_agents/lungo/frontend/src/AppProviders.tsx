/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { BrowserRouter } from "react-router-dom"
import { ThemeProvider } from "@/contexts/ThemeContext"
import { OpenUiKitThemeBridge } from "@/contexts/OpenUiKitThemeBridge"

interface AppProvidersProps {
  children: React.ReactNode
}

const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <OpenUiKitThemeBridge>{children}</OpenUiKitThemeBridge>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default AppProviders
