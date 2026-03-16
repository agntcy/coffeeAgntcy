/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Page at /agentic-workflows/:workflowId — workflow view.
 * Placeholder until workflow content is implemented.
 **/

import React from "react"
import { useParams, Link } from "react-router-dom"

const Workflow: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>()

  return (
    <div className="bg-primary-bg flex min-h-screen w-full flex-col items-center justify-center p-8">
      <h1 className="font-inter text-2xl font-semibold text-sidebar-text">
        Agentic workflow
      </h1>
      <p className="mt-4 text-sidebar-text opacity-80">
        Workflow: <span className="font-mono">{workflowId ?? "—"}</span>
      </p>
      <p className="mt-2 text-sidebar-text opacity-80">(Placeholder)</p>
      <Link
        to="/"
        className="mt-6 text-sm text-nav-text underline hover:opacity-80"
      >
        ← Back to app
      </Link>
    </div>
  )
}

export default Workflow
