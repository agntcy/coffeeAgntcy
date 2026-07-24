/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Frosted overlay shell and error state for the workflow graph canvas.
 * Used when catalog fetch or graph bootstrap fails (sidebar keeps its own inline error).
 */

import { type ReactNode } from "react"
import { Box, EmptyState } from "@open-ui-kit/core"
import type { SxProps, Theme } from "@mui/material/styles"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import { getAppShellOverlayBackgroundColor } from "./mainAreaBackground"

export const GRAPH_CANVAS_OVERLAY_ERROR_TITLE = "Workflow graph unavailable"

const graphCanvasOverlayShellSx: SxProps<Theme> = {
  position: "absolute",
  inset: 0,
  zIndex: 10,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  px: 3,
  bgcolor: (theme) => getAppShellOverlayBackgroundColor(theme),
  backdropFilter: "blur(8px)",
}

export type GraphCanvasOverlayShellProps = {
  children: ReactNode
  pointerEvents?: "auto" | "none"
}

export function GraphCanvasOverlayShell({
  children,
  pointerEvents = "auto",
}: GraphCanvasOverlayShellProps) {
  return (
    <Box sx={{ ...graphCanvasOverlayShellSx, pointerEvents }}>{children}</Box>
  )
}

export type GraphCanvasOverlayErrorProps = {
  message: string
  title?: string
}

export function GraphCanvasOverlayError({
  message,
  title = GRAPH_CANVAS_OVERLAY_ERROR_TITLE,
}: GraphCanvasOverlayErrorProps) {
  return (
    <Box
      role="alert"
      aria-live="assertive"
      sx={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        maxWidth: 480,
      }}
    >
      <EmptyState
        variant="negative"
        title={title}
        description={message}
        {...compactNegativeEmptyStateProps}
      />
    </Box>
  )
}
