/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Controls, useReactFlow } from "@xyflow/react"
import FitScreen from "@mui/icons-material/FitScreen"
import Lock from "@mui/icons-material/Lock"
import LockOpen from "@mui/icons-material/LockOpen"
import ZoomIn from "@mui/icons-material/ZoomIn"
import ZoomOut from "@mui/icons-material/ZoomOut"
import { IconButton, Stack, Tooltip } from "@open-ui-kit/core"

interface CustomControlsProps {
  isInteractive?: boolean
  onToggleInteractivity?: () => void
}

const CustomControls: React.FC<CustomControlsProps> = ({
  isInteractive = true,
  onToggleInteractivity,
}) => {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

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
        <Tooltip title="Zoom In" placement="right" arrow>
          <IconButton
            color="inherit"
            onClick={() => zoomIn()}
            aria-label="Zoom In"
          >
            <ZoomIn />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out" placement="right" arrow>
          <IconButton
            color="inherit"
            onClick={() => zoomOut()}
            aria-label="Zoom Out"
          >
            <ZoomOut />
          </IconButton>
        </Tooltip>
        <Tooltip title="Fit View" placement="right" arrow>
          <IconButton
            color="inherit"
            onClick={() => fitView({ padding: 0.45, duration: 300 })}
            aria-label="Fit View"
          >
            <FitScreen />
          </IconButton>
        </Tooltip>
        <Tooltip title={lockLabel} placement="right" arrow>
          <IconButton
            color="inherit"
            onClick={onToggleInteractivity}
            aria-label={lockLabel}
          >
            {isInteractive ? <LockOpen /> : <Lock />}
          </IconButton>
        </Tooltip>
      </Stack>
    </Controls>
  )
}

export default CustomControls
