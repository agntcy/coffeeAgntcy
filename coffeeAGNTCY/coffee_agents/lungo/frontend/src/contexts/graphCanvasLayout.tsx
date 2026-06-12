/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Layout metrics for the workflow graph canvas and `#main-content` column.
 * Used to cap portaled UI (e.g. Suggested Prompts menu) within the graph panel.
 */

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
