/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import { Controls, useReactFlow } from "@xyflow/react"
import { applyDefaultGraphView } from "@/hooks/applyDefaultGraphView"
import FitScreen from "@mui/icons-material/FitScreen"
import Lock from "@mui/icons-material/Lock"
import LockOpen from "@mui/icons-material/LockOpen"
import ZoomIn from "@mui/icons-material/ZoomIn"
import ZoomOut from "@mui/icons-material/ZoomOut"
import { Box, IconButton, Stack, Tooltip } from "@open-ui-kit/core"
import { graphNodeIconButtonSx } from "./graphNodeSurface"

interface CustomControlsProps {
  isInteractive?: boolean
  onToggleInteractivity?: () => void
}

/** MUI Tooltip requires a non-disabled element to attach pointer events. */
const TooltipControlButton: React.FC<{
  title: string
  ariaLabel: string
  disabled?: boolean
  onClick: () => void
  children: React.ReactNode
}> = ({ title, ariaLabel, disabled = false, onClick, children }) => (
  <Tooltip title={title} placement="right" arrow>
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        ...(disabled ? { pointerEvents: "none", opacity: 0.5 } : {}),
      }}
    >
      <IconButton
        size="medium"
        disabled={disabled}
        onClick={onClick}
        aria-label={ariaLabel}
        sx={(t) => graphNodeIconButtonSx(t)}
      >
        {children}
      </IconButton>
    </Box>
  </Tooltip>
)

const CustomControls: React.FC<CustomControlsProps> = ({
  isInteractive = true,
  onToggleInteractivity,
}) => {
  const { zoomIn, zoomOut, fitView, getNodes, getNodesBounds } = useReactFlow()

  const handleFitView = useCallback(() => {
    void applyDefaultGraphView({ fitView, getNodes, getNodesBounds })
  }, [fitView, getNodes, getNodesBounds])

  const lockLabel = isInteractive ? "Lock interaction" : "Unlock interaction"

  return (
    <Controls
      position="bottom-left"
      showZoom={false}
      showFitView={false}
      showInteractive={false}
    >
      <Stack
        direction="column"
        alignItems="flex-start"
        spacing={1}
        sx={{ p: 1 }}
      >
        <TooltipControlButton
          title="Zoom In"
          ariaLabel="Zoom In"
          onClick={() => zoomIn()}
        >
          <ZoomIn />
        </TooltipControlButton>
        <TooltipControlButton
          title="Zoom Out"
          ariaLabel="Zoom Out"
          onClick={() => zoomOut()}
        >
          <ZoomOut />
        </TooltipControlButton>
        <TooltipControlButton
          title="Fit View"
          ariaLabel="Fit View"
          onClick={handleFitView}
        >
          <FitScreen />
        </TooltipControlButton>
        <TooltipControlButton
          title={lockLabel}
          ariaLabel={lockLabel}
          onClick={() => onToggleInteractivity?.()}
        >
          {isInteractive ? <LockOpen /> : <Lock />}
        </TooltipControlButton>
      </Stack>
    </Controls>
  )
}

export default CustomControls
