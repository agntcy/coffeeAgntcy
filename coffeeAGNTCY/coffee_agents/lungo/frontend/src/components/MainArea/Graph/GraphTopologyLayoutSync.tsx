/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect } from "react"
import { useReactFlow, useUpdateNodeInternals } from "@xyflow/react"
import { applyDefaultGraphView } from "@/hooks/applyDefaultGraphView"

const FIT_VIEW_DELAY_MS = 200

interface GraphTopologyLayoutSyncProps {
  /** Bumped whenever agentic topology is applied to the canvas. */
  generation: number
  nodeIds: readonly string[]
  /** When true, centers and zooms the graph after handle positions are measured. */
  fitViewport: boolean
  onReady: () => void
}

/** Runs inside `<ReactFlow>` so fitView and updateNodeInternals use the live instance. */
export function GraphTopologyLayoutSync({
  generation,
  nodeIds,
  fitViewport,
  onReady,
}: GraphTopologyLayoutSyncProps) {
  const { fitView, getNodes, getNodesBounds } = useReactFlow()
  const updateNodeInternals = useUpdateNodeInternals()

  useEffect(() => {
    if (generation === 0) return

    let cancelled = false

    const run = async (): Promise<void> => {
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => {
          if (cancelled) return
          for (const id of nodeIds) {
            updateNodeInternals(id)
          }
          resolve()
        })
      })

      await new Promise((resolve) => setTimeout(resolve, FIT_VIEW_DELAY_MS))
      if (cancelled) return

      if (fitViewport) {
        await applyDefaultGraphView({ fitView, getNodes, getNodesBounds })
      }

      if (!cancelled) {
        onReady()
      }
    }

    void run()

    return () => {
      cancelled = true
    }
  }, [
    fitView,
    fitViewport,
    generation,
    getNodes,
    getNodesBounds,
    nodeIds,
    onReady,
    updateNodeInternals,
  ])

  return null
}
