/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { NODE_TYPES, EDGE_TYPES, EDGE_LABELS } from "@/utils/const"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"
import { stableAgentUuidForRecordName } from "@/utils/agenticTopologyIdentityUiMap"
function wireNode(id: string, type: string, label: string, layerIndex: number) {
  return { id, type, label, layer_index: layerIndex }
}
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

  it("honors a curated wire label2 instead of splitting the label", () => {
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Auction Agent",
            label2: "Buyer",
            layer_index: 0,
          },
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const data = nodes[0]?.data as { label1?: string; label2?: string }
    expect(data?.label1).toBe("Auction Agent")
    expect(data?.label2).toBe("Buyer")
  })

  it("falls back to splitting when wire label2 is absent or blank", () => {
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Auction Agent",
            label2: "   ",
            layer_index: 0,
          },
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const data = nodes[0]?.data as { label1?: string; label2?: string }
    expect(data?.label1).toBe("Auction")
    expect(data?.label2).toBe("Agent")
  })

  it("keeps a hidden group container with children parented and compact transport", () => {
    const groupId = "node://aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          wireNode(groupId, "group", "Logistics Group", 0),
          wireNode(
            "node://bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "customNode",
            "Buyer Logistics Agent",
            1,
          ),
          wireNode(
            "node://cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "transportNode",
            "Transport",
            2,
          ),
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const group = nodes.find((node) => node.id === groupId)
    const transport = nodes.find((node) => node.type === "transportNode")
    const child = nodes.find(
      (node) => node.type === "customNode" && node.parentId === groupId,
    )
    expect(group?.type).toBe("group")
    expect(group?.hidden).toBe(true)
    expect((group?.width ?? 0) > 0 && (group?.height ?? 0) > 0).toBe(true)
    expect(transport?.parentId).toBe(groupId)
    expect((transport?.data as { compact?: boolean })?.compact).toBe(true)
    expect(child).toBeDefined()
    expect(child?.extent).toBe("parent")
  })

  it("labels edges into MCP servers as MCP and keeps them branching", () => {
    const colombiaId = "node://10101010-1010-4101-8101-101010101010"
    const weatherId = "node://20202020-2020-4202-8202-202020202020"
    const { edges } = topologyWireToReactFlow(
      {
        nodes: [
          wireNode(colombiaId, "customNode", "Colombia Coffee Farm Agent", 0),
          wireNode(weatherId, "customNode", "Weather MCP Server", 1),
        ],
        edges: [
          {
            id: "edge://30303030-3030-4303-8303-303030303030",
            type: "branching",
            source: colombiaId,
            target: weatherId,
          },
        ],
      },
      { validateUrls: false },
    )
    expect(edges[0]?.type).toBe(EDGE_TYPES.BRANCHING)
    expect((edges[0]?.data as { label?: string })?.label).toBe(EDGE_LABELS.MCP)
  })

  it("adds A2A directory/recruiter handles and stdio edge label", () => {
    const recruiterId = "node://40404040-4040-4404-8404-404040404040"
    const directoryId = "node://50505050-5050-4505-8505-505050505050"
    const { nodes, edges } = topologyWireToReactFlow(
      {
        nodes: [
          wireNode(recruiterId, "customNode", "Agentic Recruiter", 0),
          wireNode(directoryId, "customNode", "AGNTCY Agent Directory", 1),
        ],
        edges: [
          {
            id: "edge://60606060-6060-4606-8606-606060606060",
            type: "custom",
            source: directoryId,
            target: recruiterId,
          },
        ],
      },
      { validateUrls: false },
    )
    const recruiter = nodes.find((node) => node.id === recruiterId)
    const directory = nodes.find((node) => node.id === directoryId)
    const recruiterHandles = (recruiter?.data as { extraHandles?: unknown[] })
      ?.extraHandles
    const directoryHandles = (directory?.data as { extraHandles?: unknown[] })
      ?.extraHandles
    expect(recruiterHandles).toHaveLength(1)
    expect(directoryHandles).toHaveLength(1)
    expect(edges[0]?.sourceHandle).toBe("source-left")
    expect(edges[0]?.targetHandle).toBe("target-right")
    expect((edges[0]?.data as { label?: string })?.label).toBe(
      EDGE_LABELS.MCP_WITH_STDIO,
    )
  })

  it("enrich: AGNTCY Agent Directory gets directory github link", () => {
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            type: "customNode",
            label: "AGNTCY Agent Directory",
            layer_index: 0,
          },
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const data = nodes[0]?.data as {
      githubLink?: string
      agentDirectoryLink?: string
    }
    expect(data?.githubLink).toContain("github.com")
    expect(data?.agentDirectoryLink).toBeDefined()
  })

  it("resolves relative agent_record_uri to github browse link without stable_agent_id", () => {
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Auction Agent",
            layer_index: 0,
            agent_record_uri:
              "../../agents/supervisors/auction/oasf/agents/auction-supervisor-agent.json",
          },
        ],
        edges: [],
      },
      { validateUrls: false },
    )
    const data = nodes[0]?.data as { githubLink?: string }
    expect(data?.githubLink).toContain("auction-supervisor-agent.json")
  })

  it("merges stable-agent map when stable_agent_id uses RootModel-shaped object", () => {
    const brazilUuid = stableAgentUuidForRecordName("Brazil Coffee Farm")
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Brazil Coffee Farm Agent",
            layer_index: 0,
            stable_agent_id: { root: `agent://${brazilUuid}` },
            agent_record_uri:
              "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
          },
        ],
        edges: [],
      },
      { validateUrls: false, identityUiVariant: "publish_subscribe" },
    )
    const data = nodes[0]?.data as { directoryAgentSlug?: string }
    expect(data?.directoryAgentSlug).toBe("brazil-coffee-farm")
  })

  it("merges stable-agent map: Brazil farm gets directory slug, link, and resolved github", () => {
    const brazilUuid = stableAgentUuidForRecordName("Brazil Coffee Farm")
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Brazil Coffee Farm Agent",
            layer_index: 0,
            stable_agent_id: `agent://${brazilUuid}`,
            agent_record_uri:
              "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
          },
        ],
        edges: [],
      },
      { validateUrls: false, identityUiVariant: "publish_subscribe" },
    )
    const data = nodes[0]?.data as {
      directoryAgentSlug?: string
      agentDirectoryLink?: string
      githubLink?: string
      identityAppsSlug?: string
      verificationStatus?: string
    }
    expect(data?.directoryAgentSlug).toBe("brazil-coffee-farm")
    expect(data?.agentDirectoryLink).toBeDefined()
    expect(data?.githubLink).toContain("brazil-coffee-farm.json")
    expect(data?.identityAppsSlug).toBeUndefined()
    expect(data?.verificationStatus).toBe("failed")
  })

  it("merges streaming variant github when referenceGithubUrlStreaming is set", () => {
    const brazilUuid = stableAgentUuidForRecordName("Brazil Coffee Farm")
    const { nodes } = topologyWireToReactFlow(
      {
        nodes: [
          {
            id: "node://10101010-1010-4101-8101-101010101010",
            type: "customNode",
            label: "Brazil Coffee Farm Agent",
            layer_index: 0,
            stable_agent_id: `agent://${brazilUuid}`,
            agent_record_uri:
              "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
          },
        ],
        edges: [],
      },
      { validateUrls: false, identityUiVariant: "publish_subscribe_streaming" },
    )
    const data = nodes[0]?.data as { githubLink?: string }
    expect(data?.githubLink).toContain("#L193")
  })
})
