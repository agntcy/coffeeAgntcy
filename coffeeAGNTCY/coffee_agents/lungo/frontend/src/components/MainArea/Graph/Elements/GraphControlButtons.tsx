/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared zoom / fit / lock controls for graph canvas chrome.
 */

import React, { useCallback } from "react"
import { useReactFlow } from "@xyflow/react"
import { applyDefaultGraphView } from "@/hooks/graph"
import FitScreen from "@mui/icons-material/FitScreen"
import Lock from "@mui/icons-material/Lock"
import LockOpen from "@mui/icons-material/LockOpen"
import ZoomIn from "@mui/icons-material/ZoomIn"
import ZoomOut from "@mui/icons-material/ZoomOut"
import type { SxProps, Theme } from "@mui/material/styles"
import { Box, IconButton, Stack, Tooltip } from "@open-ui-kit/core"
import { chatHeaderIconButtonSx } from "@/components/Chat/chatHeaderIconButtonSx"
import { graphCanvasIconButtonSx } from "./graphCanvasIconButtonSx"

export type GraphControlButtonVariant = "canvas" | "bar"

export interface GraphControlButtonsProps {
  direction?: "row" | "column"
  tooltipPlacement?: "top" | "right" | "bottom" | "left"
  stackSx?: SxProps<Theme>
  buttonVariant?: GraphControlButtonVariant
  isInteractive?: boolean
  onToggleInteractivity?: () => void
}

/** MUI Tooltip requires a non-disabled element to attach pointer events. */
const GraphControlTooltipButton: React.FC<{
  title: string
  ariaLabel: string
  disabled?: boolean
  onClick: () => void
  tooltipPlacement: NonNullable<GraphControlButtonsProps["tooltipPlacement"]>
  buttonVariant: GraphControlButtonVariant
  children: React.ReactNode
}> = ({
  title,
  ariaLabel,
  disabled = false,
  onClick,
  tooltipPlacement,
  buttonVariant,
  children,
}) => (
  <Tooltip title={title} placement={tooltipPlacement} arrow>
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        ...(disabled ? { pointerEvents: "none", opacity: 0.5 } : {}),
      }}
    >
      <IconButton
        {...(buttonVariant === "canvas" ? { size: "medium" as const } : {})}
        disabled={disabled}
        onClick={onClick}
        aria-label={ariaLabel}
        sx={(t) =>
          buttonVariant === "bar"
            ? chatHeaderIconButtonSx(t)
            : graphCanvasIconButtonSx(t)
        }
      >
        {children}
      </IconButton>
    </Box>
  </Tooltip>
)

const GraphControlButtons: React.FC<GraphControlButtonsProps> = ({
  direction = "column",
  tooltipPlacement = "right",
  stackSx,
  buttonVariant = "canvas",
  isInteractive = true,
  onToggleInteractivity,
}) => {
  const { zoomIn, zoomOut, fitView, getNodes, getNodesBounds } = useReactFlow()

  const handleFitView = useCallback(() => {
    void applyDefaultGraphView({ fitView, getNodes, getNodesBounds })
  }, [fitView, getNodes, getNodesBounds])

  const lockLabel = isInteractive ? "Lock interaction" : "Unlock interaction"

  return (
    <Stack
      direction={direction}
      alignItems={direction === "row" ? "center" : "flex-start"}
      spacing={direction === "row" ? 0.5 : 1}
      sx={stackSx}
    >
      <GraphControlTooltipButton
        title="Zoom In"
        ariaLabel="Zoom In"
        tooltipPlacement={tooltipPlacement}
        buttonVariant={buttonVariant}
        onClick={() => zoomIn()}
      >
        <ZoomIn />
      </GraphControlTooltipButton>
      <GraphControlTooltipButton
        title="Zoom Out"
        ariaLabel="Zoom Out"
        tooltipPlacement={tooltipPlacement}
        buttonVariant={buttonVariant}
        onClick={() => zoomOut()}
      >
        <ZoomOut />
      </GraphControlTooltipButton>
      <GraphControlTooltipButton
        title="Fit View"
        ariaLabel="Fit View"
        tooltipPlacement={tooltipPlacement}
        buttonVariant={buttonVariant}
        onClick={handleFitView}
      >
        <FitScreen />
      </GraphControlTooltipButton>
      <GraphControlTooltipButton
        title={lockLabel}
        ariaLabel={lockLabel}
        tooltipPlacement={tooltipPlacement}
        buttonVariant={buttonVariant}
        onClick={() => onToggleInteractivity?.()}
      >
        {isInteractive ? <LockOpen /> : <Lock />}
      </GraphControlTooltipButton>
    </Stack>
  )
}

export default GraphControlButtons
