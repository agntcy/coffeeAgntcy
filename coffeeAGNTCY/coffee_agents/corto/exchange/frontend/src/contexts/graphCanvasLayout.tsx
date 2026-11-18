/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { createContext, useContext } from "react"

export interface GraphCanvasLayoutMetrics {
  graphCanvasWidth?: number
  mainContentLeft?: number
  mainContentWidth?: number
}

export const GraphCanvasLayoutContext = createContext<GraphCanvasLayoutMetrics>(
  {},
)

export function useGraphCanvasLayout(): GraphCanvasLayoutMetrics {
  return useContext(GraphCanvasLayoutContext)
}
