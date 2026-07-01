/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Edge, Node } from "@xyflow/react"
import { describe, expect, it } from "vitest"
import {
  A2A_HTTP_CONFIG,
  GROUP_MESSAGING_CONFIG,
} from "@/utils/graphConfigsData"
import { NODE_IDS } from "@/utils/const"
import {
  animationSequenceStepIds,
  deriveAnimationSequenceFromGraph,
  resolveStreamAuthorToNodeId,
} from "./chatStreamGraphHighlight"

describe("resolveStreamAuthorToNodeId", () => {
  it.each([
    {
      caseName: "recruiter author -> live recruiter node via slug",
      author: "recruiter_service",
      config: A2A_HTTP_CONFIG,
      expected: NODE_IDS.RECRUITER,
    },
    {
      caseName: "directory author -> live directory node via slug",
      author: "directory",
      config: A2A_HTTP_CONFIG,
      expected: NODE_IDS.DIRECTORY,
    },
    {
      caseName: "group supervisor -> buyer node via label fallback",
      author: "Supervisor",
      config: GROUP_MESSAGING_CONFIG,
      expected: NODE_IDS.AUCTION_AGENT,
    },
  ])("$caseName", ({ author, config, expected }) => {
    expect(resolveStreamAuthorToNodeId(author, config)).toBe(expected)
  })

  it("returns null without a live graph to resolve against", () => {
    expect(resolveStreamAuthorToNodeId("recruiter_service")).toBeNull()
  })
})

describe("animationSequenceStepIds", () => {
  it("returns ids for a valid step index", () => {
    expect(animationSequenceStepIds(GROUP_MESSAGING_CONFIG, 0)).toEqual([
      NODE_IDS.AUCTION_AGENT,
    ])
  })

  it("returns empty when step is out of range", () => {
    expect(animationSequenceStepIds(GROUP_MESSAGING_CONFIG, 99)).toEqual([])
  })
})

function liveNode(
  id: string,
  type: string,
  data: Record<string, unknown>,
): Node {
  return { id, type, position: { x: 0, y: 0 }, data }
}

function liveEdge(id: string, source: string, target: string): Edge {
  return { id, source, target }
}

describe("deriveAnimationSequenceFromGraph", () => {
  const nodes: Node[] = [
    liveNode("agent://auction", "customNode", {}),
    liveNode("transport://slim", "transportNode", {}),
    liveNode("agent://brazil", "customNode", {}),
    liveNode("agent://colombia", "customNode", {}),
    liveNode("agent://vietnam", "customNode", {}),
    liveNode("agent://weather", "customNode", {}),
    liveNode("agent://payment", "customNode", {}),
  ]
  const edges: Edge[] = [
    liveEdge("e-auction-transport", "agent://auction", "transport://slim"),
    liveEdge("e-transport-brazil", "transport://slim", "agent://brazil"),
    liveEdge("e-transport-colombia", "transport://slim", "agent://colombia"),
    liveEdge("e-transport-vietnam", "transport://slim", "agent://vietnam"),
    liveEdge("e-colombia-weather", "agent://colombia", "agent://weather"),
    liveEdge("e-colombia-payment", "agent://colombia", "agent://payment"),
  ]

  it("pulses root, fan-out edges, then each next layer", () => {
    const seq = deriveAnimationSequenceFromGraph(nodes, edges)
    expect(seq.map((step) => step.ids)).toEqual([
      ["agent://auction"],
      ["e-auction-transport"],
      ["transport://slim"],
      ["e-transport-brazil", "e-transport-colombia", "e-transport-vietnam"],
      ["agent://brazil", "agent://colombia", "agent://vietnam"],
      ["e-colombia-weather", "e-colombia-payment"],
      ["agent://weather", "agent://payment"],
    ])
  })

  it("returns empty without edges and skips isolated container nodes", () => {
    expect(deriveAnimationSequenceFromGraph(nodes, [])).toEqual([])
    const withContainer = deriveAnimationSequenceFromGraph(
      [liveNode("group://logistics", "group", {}), ...nodes],
      edges,
    )
    expect(withContainer[0].ids).toEqual(["agent://auction"])
  })

  it("roots at a non-transport node (a2a recruiter -> directory chain)", () => {
    const seq = deriveAnimationSequenceFromGraph(
      [
        liveNode("agent://recruiter", "customNode", {}),
        liveNode("agent://directory", "customNode", {}),
      ],
      [
        liveEdge(
          "e-recruiter-directory",
          "agent://recruiter",
          "agent://directory",
        ),
      ],
    )
    expect(seq.map((step) => step.ids)).toEqual([
      ["agent://recruiter"],
      ["e-recruiter-directory"],
      ["agent://directory"],
    ])
  })

  it("returns empty for a cyclic graph with no root", () => {
    const seq = deriveAnimationSequenceFromGraph(
      [
        liveNode("agent://a", "customNode", {}),
        liveNode("agent://b", "customNode", {}),
      ],
      [
        liveEdge("e-a-b", "agent://a", "agent://b"),
        liveEdge("e-b-a", "agent://b", "agent://a"),
      ],
    )
    expect(seq).toEqual([])
  })
})
