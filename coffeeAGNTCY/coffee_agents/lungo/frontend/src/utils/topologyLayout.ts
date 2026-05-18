/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

const Y_GAP = 200
const X_GAP = 280
const ORIGIN_X = 400
const ORIGIN_Y = 60

export function layoutPositionsByLayer(
  nodeIds: string[],
  layerById: Map<string, number>,
): Map<string, { x: number; y: number }> {
  const byLayer = new Map<number, string[]>()
  for (const id of nodeIds) {
    const layer = layerById.get(id) ?? 0
    if (!byLayer.has(layer)) byLayer.set(layer, [])
    byLayer.get(layer)!.push(id)
  }
  const layers = [...byLayer.keys()].sort((a, b) => a - b)
  const out = new Map<string, { x: number; y: number }>()
  for (const layer of layers) {
    const ids = byLayer.get(layer)!
    const y = ORIGIN_Y + layer * Y_GAP
    const totalWidth = (ids.length - 1) * X_GAP
    const x0 = ORIGIN_X - totalWidth / 2
    ids.forEach((id, i) => {
      out.set(id, { x: x0 + i * X_GAP, y })
    })
  }
  return out
}
