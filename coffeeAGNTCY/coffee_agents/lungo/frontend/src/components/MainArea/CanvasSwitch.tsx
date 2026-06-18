/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react"
import MainArea from "./MainArea"
import PatternDocCanvas from "./PatternDocCanvas"
import type { MainAreaProps } from "./useMainArea"
import type { CanvasMode, PatternDocState } from "@/types/patternDoc"

export interface CanvasSwitchProps extends MainAreaProps {
  canvasMode?: CanvasMode
  selectedReferencePattern?: string | null
  patternDocState?: PatternDocState
}

const CanvasSwitch: React.FC<CanvasSwitchProps> = ({
  canvasMode,
  selectedReferencePattern,
  patternDocState,
  ...mainAreaProps
}) => {
  if (
    canvasMode === "pattern_doc" &&
    typeof selectedReferencePattern === "string" &&
    patternDocState !== undefined
  ) {
    return (
      <PatternDocCanvas
        selectedReferencePattern={selectedReferencePattern}
        patternDocState={patternDocState}
      />
    )
  }
  return <MainArea {...mainAreaProps} />
}

export default CanvasSwitch
