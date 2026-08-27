/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  messagingHighlightIdsFromTopology,
  patchGraphActiveHighlight,
} from "@/utils/workflowEventMessagingHighlight"

describe("workflowEventMessagingHighlight", () => {
  it("highlights edge-only partial with resolved catalog edge id", () => {
    const catalogEdgeId = "edge://1a000001-0001-4000-a001-e00000000005"
    const sourceSid = "agent://colombia-farm-stable"
    const targetSid = "agent://weather-mcp-stable"
    const partial = {
      nodes: [],
      edges: [
        {
          id: catalogEdgeId,
          source: "node://colombia-wire",
          target: "node://weather-wire",
        },
      ],
    }

    const ids = messagingHighlightIdsFromTopology(partial)
    expect(ids.nodeIds.size).toBe(0)
    expect(ids.edgeIds.has(catalogEdgeId)).toBe(true)
    expect(
      ids.edgePairs.has(`${sourceSid}->${targetSid}`) ||
        ids.edgePairs.has("node://colombia-wire->node://weather-wire"),
    ).toBe(true)

    const edges = [
      {
        id: catalogEdgeId,
        source: sourceSid,
        target: targetSid,
        animated: false,
        data: {},
      },
    ]
    const { edges: highlighted } = patchGraphActiveHighlight([], edges, ids)
    expect(highlighted[0]?.animated).toBe(true)
  })

  it("indexes stable agent id pairs from edge wire fields", () => {
    const sourceSid = "agent://colombia-farm-stable"
    const targetSid = "agent://weather-mcp-stable"
    const ids = messagingHighlightIdsFromTopology({
      nodes: [],
      edges: [
        {
          id: "edge://catalog-mcp",
          source: "node://colombia-wire",
          target: "node://weather-wire",
          source_stable_agent_id: sourceSid,
          target_stable_agent_id: targetSid,
        },
      ],
    })

    expect(ids.edgePairs.has(`${sourceSid}->${targetSid}`)).toBe(true)
  })
})
