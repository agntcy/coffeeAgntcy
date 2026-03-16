/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import App from "./App"
import AppProviders from "./AppProviders"
import "./index.css"

const rootElement = document.getElementById("root")
if (!rootElement) throw new Error("Failed to find the root element")

createRoot(rootElement).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
)
