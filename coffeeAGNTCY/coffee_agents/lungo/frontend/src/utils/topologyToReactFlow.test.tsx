/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { NODE_TYPES, EDGE_TYPES } from "@/utils/const"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"

describe("topologyWireToReactFlow", () => {
  it.each([
    {
      caseName: "full topology with custom and transport nodes",
      topology: {
        nodes: [
          {
            id: "node://11111111-1111-4111-8111-111111111111",
            operation: "read",
            type: "customNode",
            label: "Auction Supervisor",
            size: { width: 1, height: 1 },
            layer_index: 0,
          },
          {
            id: "node://22222222-2222-4222-8222-222222222222",
            operation: "read",
            type: "transportNode",
            label: "Transport",
            size: { width: 1, height: 1 },
            layer_index: 1,
          },
        ],
        edges: [
          {
            id: "edge://33333333-3333-4333-8333-333333333333",
            operation: "read",
            type: "custom",
            source: "node://11111111-1111-4111-8111-111111111111",
            target: "node://22222222-2222-4222-8222-222222222222",
            bidirectional: false,
            weight: 1,
          },
        ],
      },
      expectNodeCount: 2,
      expectEdgeCount: 1,
      firstNodeType: NODE_TYPES.CUSTOM,
      transportNodeType: NODE_TYPES.TRANSPORT,
    },
    {
      caseName: "empty edges array",
      topology: {
        nodes: [
          {
            id: "node://aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            operation: "read",
            type: "customNode",
            label: "Only Node",
            layer_index: 0,
          },
        ],
        edges: [],
      },
      expectNodeCount: 1,
      expectEdgeCount: 0,
      firstNodeType: NODE_TYPES.CUSTOM,
      transportNodeType: null,
    },
    {
      caseName: "branching edge type preserved",
      topology: {
        nodes: [
          {
            id: "node://bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            type: "customNode",
            label: "A",
            layer_index: 0,
          },
          {
            id: "node://cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            type: "customNode",
            label: "B",
            layer_index: 1,
          },
        ],
        edges: [
          {
            id: "edge://dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            type: "branching",
            source: "node://bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            target: "node://cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            branches: ["node://cccccccc-cccc-4ccc-8ccc-cccccccccccc"],
          },
        ],
      },
      expectNodeCount: 2,
      expectEdgeCount: 1,
      firstNodeType: NODE_TYPES.CUSTOM,
      transportNodeType: null,
      edgeType: EDGE_TYPES.BRANCHING,
    },
    {
      caseName: "unknown edge type falls back to custom",
      topology: {
        nodes: [
          {
            id: "node://eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            type: "customNode",
            label: "X",
            layer_index: 0,
          },
          {
            id: "node://ffffffff-ffff-4fff-8fff-ffffffffffff",
            type: "customNode",
            label: "Y",
            layer_index: 0,
          },
        ],
        edges: [
          {
            id: "edge://99999999-9999-4999-8999-999999999999",
            type: "weird-edge",
            source: "node://eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            target: "node://ffffffff-ffff-4fff-8fff-ffffffffffff",
          },
        ],
      },
      expectNodeCount: 2,
      expectEdgeCount: 1,
      firstNodeType: NODE_TYPES.CUSTOM,
      transportNodeType: null,
      edgeType: EDGE_TYPES.CUSTOM,
    },
  ])(
    "$caseName",
    ({
      topology,
      expectNodeCount,
      expectEdgeCount,
      firstNodeType,
      transportNodeType,
      edgeType,
    }) => {
      const { nodes, edges } = topologyWireToReactFlow(topology, {
        validateUrls: false,
      })
      expect(nodes).toHaveLength(expectNodeCount)
      expect(edges).toHaveLength(expectEdgeCount)
      expect(nodes[0]?.type).toBe(firstNodeType)
      if (transportNodeType) {
        expect(nodes[1]?.type).toBe(transportNodeType)
      }
      if (edgeType) {
        expect(edges[0]?.type).toBe(edgeType)
      }
    },
  )

  it("splits single label into label1 and label2", () => {
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Brazil Farm Agent",
            layer_index: 0,
          },
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const data = nodes[0]?.data as { label1?: string; label2?: string }
    expect(data?.label1).toBe("Brazil")
    expect(data?.label2).toBe("Farm Agent")
  })
})
