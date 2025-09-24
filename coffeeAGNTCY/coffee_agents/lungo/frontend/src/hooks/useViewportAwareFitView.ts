/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback } from "react"
import { useReactFlow } from "@xyflow/react"

interface ViewportAwareFitViewOptions {
  chatHeight: number
  isExpanded: boolean
}

export const useViewportAwareFitView = () => {
  const { fitView } = useReactFlow()

  const fitViewWithViewportLogic = useCallback(
    ({ chatHeight, isExpanded }: ViewportAwareFitViewOptions) => {
      const viewportHeight = window.innerHeight
      const viewportWidth = window.innerWidth

      const availableHeight = viewportHeight - chatHeight - 40
      const availableWidth = viewportWidth - 320

      let padding: number
      if (availableHeight < 400 || availableWidth < 600) {
        padding = 0.15
      } else if (availableHeight < 600 || availableWidth < 800) {
        padding = 0.25
      } else {
        padding = 0.35
      }

      let minZoom: number
      let maxZoom: number

      if (isExpanded) {
        minZoom = Math.max(0.4, availableHeight / 1200)
        maxZoom = Math.min(1.8, availableWidth / 600)
      } else {
        minZoom = 0.6
        maxZoom = 1.8
      }

      fitView({
        padding,
        duration: 300,
        minZoom,
        maxZoom,
      })
    },
    [fitView],
  )

  return fitViewWithViewportLogic
}
