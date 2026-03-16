/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Page at /use-cases — list use cases.
 * Placeholder until use-case list is implemented.
 **/

import React from "react"
import { Link } from "react-router-dom"

const UseCases: React.FC = () => {
  return (
    <div className="bg-primary-bg flex min-h-screen w-full flex-col items-center justify-center p-8">
      <h1 className="font-inter text-2xl font-semibold text-sidebar-text">
        Use cases
      </h1>
      <p className="mt-4 text-sidebar-text opacity-80">
        List of use cases. (Placeholder)
      </p>
      <Link
        to="/"
        className="mt-6 text-sm text-nav-text underline hover:opacity-80"
      >
        ← Back to app
      </Link>
    </div>
  )
}

export default UseCases
