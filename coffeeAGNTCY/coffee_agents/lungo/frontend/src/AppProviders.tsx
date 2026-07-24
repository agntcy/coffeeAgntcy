/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { BrowserRouter } from "react-router-dom"
import { OpenUiKitThemeBridge } from "@/contexts/OpenUiKitThemeBridge"
import ErrorBoundary from "@/errors/ui/ErrorBoundary"
import { ErrorNotifications } from "@/errors/ui"

interface AppProvidersProps {
  children: React.ReactNode
}

const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <OpenUiKitThemeBridge>
        <ErrorNotifications />
        <ErrorBoundary source="App" useReload>
          {children}
        </ErrorBoundary>
      </OpenUiKitThemeBridge>
    </BrowserRouter>
  )
}

export default AppProviders
