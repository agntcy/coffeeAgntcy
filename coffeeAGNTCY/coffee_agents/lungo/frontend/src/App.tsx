/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import { RootPage } from "@/pages"

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<RootPage />} />
      {/* <Route path="/agentic-workflows/:workflowId" element={<Workflow />} /> */}
      {/* <Route path="/patterns" element={<Patterns />} /> */}
      {/* <Route path="/use-cases" element={<UseCases />} /> */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
