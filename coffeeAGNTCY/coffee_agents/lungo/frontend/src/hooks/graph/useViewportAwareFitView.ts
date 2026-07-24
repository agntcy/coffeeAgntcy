/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback } from "react"
import { useReactFlow } from "@xyflow/react"
import { applyDefaultGraphView } from "./applyDefaultGraphView"

export const useViewportAwareFitView = () => {
  const { fitView, getNodes, getNodesBounds } = useReactFlow()

  const fitViewWithViewportLogic = useCallback(() => {
    void applyDefaultGraphView({ fitView, getNodes, getNodesBounds })
  }, [fitView, getNodes, getNodesBounds])

  return fitViewWithViewportLogic
}
