/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Box, EmptyState, GeneralSize } from "@open-ui-kit/core"

const DEFAULT_TITLE = "Something went wrong"
const DEFAULT_DESCRIPTION = "An unexpected error occurred. Please try again."

function getErrorDescription(error: Error): string {
  const message = error.message.trim()
  return message || DEFAULT_DESCRIPTION
}

export type ErrorFallbackProps = {
  error: Error
  title?: string
  compact?: boolean
  actionTitle: string
  onAction: () => void
}

const ErrorFallback = ({
  error,
  title,
  compact = false,
  actionTitle,
  onAction,
}: ErrorFallbackProps) => (
  <Box
    role="alert"
    aria-live="assertive"
    sx={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      width: "100%",
      height: compact ? "100%" : "100vh",
      minHeight: compact ? 200 : undefined,
      p: compact ? 2 : 4,
      boxSizing: "border-box",
    }}
  >
    <EmptyState
      variant="negative"
      hideIllustration
      size={compact ? GeneralSize.Medium : GeneralSize.Large}
      title={title ?? DEFAULT_TITLE}
      description={getErrorDescription(error)}
      actionTitle={actionTitle}
      actionCallback={onAction}
    />
  </Box>
)

export default ErrorFallback
