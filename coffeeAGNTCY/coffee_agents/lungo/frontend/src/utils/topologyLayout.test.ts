/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import { describe, expect, it } from "vitest"
import { NODE_IDS, NODE_TYPES } from "@/utils/const"
import { CUSTOM_NODE_WIDTH } from "@/utils/graphNodeDimensions"
import { getGraphConfig } from "@/utils/graphConfigs"
import {
  CUSTOM_NODE_X_GAP,
  TRANSPORT_NODE_WIDTH_BAR,
  TRANSPORT_NODE_WIDTH_COMPACT,
  bucketNodeLayerY,
  centerCustomNodesOnTransport,
  layoutSlimTransportGraph,
  optimizeBarTransportEdgeHandles,
} from "@/utils/topologyLayout"

describe("centerCustomNodesOnTransport", () => {
  it("does not move nodes when transport is compact", () => {
    const transportId = "transport://slim"
    const leftAgent = "agent-left"
    const rightAgent = "agent-right"
    const positions = new Map([
      [transportId, { x: 380, y: 270 }],
      [leftAgent, { x: 150, y: 100 }],
      [rightAgent, { x: 550, y: 100 }],
    ])
    const layerById = new Map([
      [transportId, 2],
      [leftAgent, 1],
      [rightAgent, 1],
    ])

    centerCustomNodesOnTransport(positions, layerById, transportId, {
      transportCompact: true,
    })

    expect(positions.get(leftAgent)).toEqual({ x: 150, y: 100 })
    expect(positions.get(rightAgent)).toEqual({ x: 550, y: 100 })
  })

  it("redistributes a layer with MCP spacing centered on bar transport", () => {
    const transportId = "transport://slim"
    const leftAgent = "agent-left"
    const centerAgent = "agent-center"
    const rightAgent = "agent-right"
    const positions = new Map([
      [transportId, { x: 100, y: 270 }],
      [leftAgent, { x: 150, y: 400 }],
      [centerAgent, { x: 500, y: 400 }],
      [rightAgent, { x: 900, y: 400 }],
    ])
    const layerById = new Map([
      [transportId, 2],
      [leftAgent, 1],
      [centerAgent, 1],
      [rightAgent, 1],
    ])

    centerCustomNodesOnTransport(positions, layerById, transportId, {
      transportCompact: false,
    })

    const transportCenterX = 100 + TRANSPORT_NODE_WIDTH_BAR / 2
    const leftCenter = positions.get(leftAgent)!.x + CUSTOM_NODE_WIDTH / 2
    const centerCenter = positions.get(centerAgent)!.x + CUSTOM_NODE_WIDTH / 2
    const rightCenter = positions.get(rightAgent)!.x + CUSTOM_NODE_WIDTH / 2

    expect(centerCenter).toBeCloseTo(transportCenterX, 5)
    expect(leftCenter - centerCenter).toBeCloseTo(-CUSTOM_NODE_X_GAP, 5)
    expect(rightCenter - centerCenter).toBeCloseTo(CUSTOM_NODE_X_GAP, 5)
  })

  it("keeps farm nodes on slightly different y values in one layer", () => {
    expect(bucketNodeLayerY(503.93)).toBe(bucketNodeLayerY(505.38))
  })
})

describe("layoutSlimTransportGraph (bar)", () => {
  it("spaces Brazil, Colombia, and Vietnam without overlap", () => {
    const nodes: Node[] = [
      {
        id: NODE_IDS.TRANSPORT,
        type: NODE_TYPES.TRANSPORT,
        position: { x: 229, y: 284 },
        data: { compact: false },
      },
      {
        id: NODE_IDS.BRAZIL_FARM,
        type: NODE_TYPES.CUSTOM,
        position: { x: 232, y: 503.93 },
        data: {},
      },
      {
        id: NODE_IDS.COLOMBIA_FARM,
        type: NODE_TYPES.CUSTOM,
        position: { x: 521, y: 505.38 },
        data: {},
      },
      {
        id: NODE_IDS.VIETNAM_FARM,
        type: NODE_TYPES.CUSTOM,
        position: { x: 832, y: 505.08 },
        data: {},
      },
    ]

    const { nodes: laidOut } = layoutSlimTransportGraph(nodes, [])
    const byId = new Map(laidOut.map((node) => [node.id, node]))
    const brazil = byId.get(NODE_IDS.BRAZIL_FARM)!
    const colombia = byId.get(NODE_IDS.COLOMBIA_FARM)!
    const vietnam = byId.get(NODE_IDS.VIETNAM_FARM)!

    expect(colombia.position.x - brazil.position.x).toBeCloseTo(
      CUSTOM_NODE_X_GAP,
      5,
    )
    expect(vietnam.position.x - colombia.position.x).toBeCloseTo(
      CUSTOM_NODE_X_GAP,
      5,
    )
    expect(colombia.position.x - brazil.position.x).toBeGreaterThan(
      CUSTOM_NODE_WIDTH,
    )
  })
})

describe("optimizeBarTransportEdgeHandles", () => {
  const transportId = "transport"
  const auctionId = "auction"
  const brazilId = "brazil"
  const colombiaId = "colombia"
  const vietnamId = "vietnam"

  const nodes: Node[] = [
    {
      id: auctionId,
      type: NODE_TYPES.CUSTOM,
      position: { x: 500, y: 50 },
      data: {},
    },
    {
      id: transportId,
      type: NODE_TYPES.TRANSPORT,
      position: { x: 100, y: 200 },
      data: { compact: false },
    },
    {
      id: brazilId,
      type: NODE_TYPES.CUSTOM,
      position: { x: 150, y: 400 },
      data: {},
    },
    {
      id: colombiaId,
      type: NODE_TYPES.CUSTOM,
      position: { x: 500, y: 400 },
      data: {},
    },
    {
      id: vietnamId,
      type: NODE_TYPES.CUSTOM,
      position: { x: 850, y: 400 },
      data: {},
    },
  ]

  const edges: Edge[] = [
    {
      id: "auction-transport",
      source: auctionId,
      target: transportId,
      targetHandle: "top",
    },
    {
      id: "transport-brazil",
      source: transportId,
      target: brazilId,
      sourceHandle: "bottom_right",
    },
    {
      id: "transport-colombia",
      source: transportId,
      target: colombiaId,
      sourceHandle: "bottom_left",
    },
    {
      id: "transport-vietnam",
      source: transportId,
      target: vietnamId,
      sourceHandle: "bottom_center",
    },
  ]

  it("assigns handles left-to-right to avoid crossings", () => {
    const optimized = optimizeBarTransportEdgeHandles(nodes, edges, transportId)
    const byId = new Map(optimized.map((edge) => [edge.id, edge]))

    expect(byId.get("auction-transport")?.targetHandle).toBe("top_center")
    expect(byId.get("transport-brazil")?.sourceHandle).toBe("bottom_left")
    expect(byId.get("transport-colombia")?.sourceHandle).toBe("bottom_center")
    expect(byId.get("transport-vietnam")?.sourceHandle).toBe("bottom_right")
  })
})

describe("graphNodeDimensions", () => {
  it("uses outer card width including CustomNode padding", () => {
    expect(CUSTOM_NODE_WIDTH).toBe(194)
  })
})

describe("layoutSlimTransportGraph (compact group)", () => {
  it("centers transport and custom rows with equal group margins", () => {
    const config = getGraphConfig("group_messaging")
    const group = config.nodes.find((node) => node.type === NODE_TYPES.GROUP)!
    const groupWidth = group.style?.width as number
    const transport = config.nodes.find(
      (node) => node.id === NODE_IDS.TRANSPORT,
    )!
    const customs = config.nodes.filter(
      (node) => node.parentId === group.id && node.type === NODE_TYPES.CUSTOM,
    )

    expect(transport.position.x).toBeCloseTo(
      (groupWidth - TRANSPORT_NODE_WIDTH_COMPACT) / 2,
      5,
    )

    const layerYs = [...new Set(customs.map((node) => node.position.y))]
    for (const layerY of layerYs) {
      const row = customs.filter((node) => node.position.y === layerY)
      const leftX = Math.min(...row.map((node) => node.position.x))
      const rightX = Math.max(
        ...row.map((node) => node.position.x + CUSTOM_NODE_WIDTH),
      )
      expect(leftX).toBeCloseTo(groupWidth - rightX, 5)
    }
  })
})
