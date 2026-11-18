/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback } from "react"
import { useReactFlow } from "@xyflow/react"
import { applyDefaultGraphView } from "@/hooks/graph/applyDefaultGraphView"

export const useViewportAwareFitView = () => {
  const { fitView, getNodes, getNodesBounds } = useReactFlow()

  return useCallback(() => {
    void applyDefaultGraphView({ fitView, getNodes, getNodesBounds })
  }, [fitView, getNodes, getNodesBounds])
}
