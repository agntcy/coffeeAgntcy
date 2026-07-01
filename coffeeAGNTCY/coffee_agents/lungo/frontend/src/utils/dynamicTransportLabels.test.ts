/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Edge, Node } from "@xyflow/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { EDGE_LABELS } from "@/utils/const"
import {
  applyDynamicTransportLabels,
  transportGithubLink,
} from "@/utils/dynamicTransportLabels"

const SDK = LUNGO_FRONTEND_URLS.github.appSdkBaseUrl
const REGULAR = LUNGO_FRONTEND_URLS.github.transports.regular

describe("transportGithubLink", () => {
  it.each([
    {
      caseName: "SLIM regular -> slim link",
      transport: "SLIM",
      isStreaming: false,
      expected: `${SDK}${REGULAR.slim}`,
    },
    {
      caseName: "NATS regular -> nats link",
      transport: "NATS",
      isStreaming: false,
      expected: `${SDK}${REGULAR.nats}`,
    },
    {
      caseName: "SLIM streaming -> streaming slim link",
      transport: "SLIM",
      isStreaming: true,
      expected: `${SDK}${LUNGO_FRONTEND_URLS.github.transports.streaming.slim}`,
    },
    {
      caseName: "unknown transport -> general link",
      transport: "KAFKA",
      isStreaming: false,
      expected: `${SDK}${LUNGO_FRONTEND_URLS.github.transports.general}`,
    },
  ])("$caseName", ({ transport, isStreaming, expected }) => {
    expect(transportGithubLink(transport, isStreaming)).toBe(expected)
  })
})

function transportNode(id: string): Node {
  return {
    id,
    type: "transportNode",
    position: { x: 0, y: 0 },
    data: { label: "Transport" },
  }
}

function mcpEdge(id: string): Edge {
  return { id, source: "a", target: "b", data: { label: "MCP: " } }
}

function stdioEdge(id: string): Edge {
  return {
    id,
    source: "a",
    target: "b",
    data: { label: EDGE_LABELS.MCP_WITH_STDIO },
  }
}

describe("applyDynamicTransportLabels", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ transport: "SLIM" }),
    }))
    vi.stubGlobal("fetch", fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("skips patterns without a transport config endpoint", async () => {
    let nodes: Node[] = [transportNode("t")]
    const setNodes = (updater: (n: Node[]) => Node[]) => {
      nodes = updater(nodes)
    }
    const setEdges = (updater: (e: Edge[]) => Edge[]) => updater([])

    await applyDynamicTransportLabels(setNodes, setEdges, "group_messaging")

    expect(fetchMock).not.toHaveBeenCalled()
    expect(nodes[0].data.label).toBe("Transport")
  })

  it("patches transport nodes + MCP edges and caches the fetch", async () => {
    let nodes: Node[] = [transportNode("transport://transport")]
    let edges: Edge[] = [mcpEdge("e1")]
    const setNodes = (updater: (n: Node[]) => Node[]) => {
      nodes = updater(nodes)
    }
    const setEdges = (updater: (e: Edge[]) => Edge[]) => {
      edges = updater(edges)
    }

    await applyDynamicTransportLabels(
      setNodes,
      setEdges,
      "publish_subscribe",
      false,
    )

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(nodes[0].data.label).toBe("Transport: SLIM")
    expect(nodes[0].data.githubLink).toBe(`${SDK}${REGULAR.slim}`)
    expect(edges[0].data?.label).toBe("MCP: SLIM")

    const nodesRef = nodes
    const edgesRef = edges
    await applyDynamicTransportLabels(
      setNodes,
      setEdges,
      "publish_subscribe",
      false,
    )

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(nodes).toBe(nodesRef)
    expect(edges).toBe(edgesRef)
  })

  it("patches plain MCP edges but leaves the MCP_WITH_STDIO label intact", async () => {
    let edges: Edge[] = [mcpEdge("plain"), stdioEdge("stdio")]
    const setNodes = (updater: (n: Node[]) => Node[]) => updater([])
    const setEdges = (updater: (e: Edge[]) => Edge[]) => {
      edges = updater(edges)
    }

    await applyDynamicTransportLabels(
      setNodes,
      setEdges,
      "publish_subscribe",
      false,
    )

    expect(edges[0].data?.label).toBe("MCP: SLIM")
    expect(edges[1].data?.label).toBe(EDGE_LABELS.MCP_WITH_STDIO)
  })
})
