/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { type ReactNode } from "react"
import {
  ErrorBoundary as ReactErrorBoundary,
  type FallbackProps,
} from "react-error-boundary"
import ErrorFallback from "./ErrorFallback"
import { reportUiError } from "./reportUiError"

function toError(value: unknown): Error {
  return value instanceof Error ? value : new Error(String(value))
}

export type ErrorBoundaryProps = {
  children: ReactNode
  /** Label used in logs and optional fallback title override. */
  source?: string
  fallbackTitle?: string
  /** When these values change, the boundary clears its error state. */
  resetKeys?: readonly unknown[]
  /** Compact layout for nested boundaries (e.g. graph section). */
  compact?: boolean
  /** Primary action reloads the page instead of resetting boundary state. */
  useReload?: boolean
}

const ErrorBoundary = ({
  children,
  source,
  fallbackTitle,
  resetKeys,
  compact = false,
  useReload = false,
}: ErrorBoundaryProps) => {
  const renderFallback = ({ error, resetErrorBoundary }: FallbackProps) => (
    <ErrorFallback
      error={toError(error)}
      title={fallbackTitle}
      compact={compact}
      actionTitle={useReload ? "Reload page" : "Try again"}
      onAction={useReload ? () => window.location.reload() : resetErrorBoundary}
    />
  )

  return (
    <ReactErrorBoundary
      resetKeys={resetKeys ? [...resetKeys] : undefined}
      onError={(error, info) => {
        const normalizedError = toError(error)

        reportUiError({
          title: fallbackTitle ?? "Application error",
          message:
            normalizedError.message || "An unexpected render error occurred",
          source: source ?? "ErrorBoundary",
          componentStack: info.componentStack || undefined,
          notify: false,
        })
      }}
      fallbackRender={renderFallback}
    >
      {children}
    </ReactErrorBoundary>
  )
}

export default ErrorBoundary
