/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Controls, ControlButton, useReactFlow } from "@xyflow/react"
import { Lock, Unlock } from "lucide-react"

interface CustomControlsProps {
  isInteractive?: boolean
  onToggleInteractivity?: () => void
}

const CustomControls: React.FC<CustomControlsProps> = ({
  isInteractive = true,
  onToggleInteractivity,
}) => {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  return (
    <Controls showZoom={false} showFitView={false} showInteractive={false}>
      <ControlButton
        onClick={() => zoomIn()}
        title="Zoom In"
        aria-label="Zoom In"
      >
        <span className="text-base font-normal">+</span>
      </ControlButton>
      <ControlButton
        onClick={() => zoomOut()}
        title="Zoom Out"
        aria-label="Zoom Out"
      >
        <span className="text-base font-normal">−</span>
      </ControlButton>
      <ControlButton
        onClick={() => fitView({ padding: 0.45, duration: 300 })}
        title="Fit View"
        aria-label="Fit View"
      >
        <span className="text-base font-normal">⛶</span>
      </ControlButton>
      <ControlButton
        onClick={onToggleInteractivity}
        title={isInteractive ? "Lock interaction" : "Unlock interaction"}
        aria-label={isInteractive ? "Lock interaction" : "Unlock interaction"}
      >
        {isInteractive ? (
          <Unlock className="h-4 w-4" />
        ) : (
          <Lock className="h-4 w-4" />
        )}
      </ControlButton>
    </Controls>
  )
}

export default CustomControls
