/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { NODE_TYPES } from "@/utils/const"
import { customNodeDataFromNode } from "@/components/MainArea/Graph/Elements/customNodeData"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"

const SEED_RECRUITER = "node://4a000001-0001-4000-a001-000000000001"
const ANCHOR = "node://6f1d2c3a-0000-4000-8000-000000000001"
const DISCOVERED = "node://6f1d2c3a-0000-4000-8000-000000000002"
const DISCOVERED_SID = "agent://9a6cc736-d6fb-5a3e-82d6-3552d09b5ae9"

/**
 * The recruiter emits an anchor node sharing the seeded "Agentic Recruiter"
 * label (no stable id) so it dedups onto the seed and the discovered-agent
 * edge re-points there, plus the discovered node carrying its OASF record.
 */
describe("topologyWireToReactFlow discovery merge", () => {
  const record = { name: "Brazil", url: "http://brazil:9000" }
  const { nodes, edges } = topologyWireToReactFlow(
    {
      nodes: [
        {
          id: SEED_RECRUITER,
          type: "customNode",
          label: "Agentic Recruiter",
          layer_index: 0,
          agent_record_uri:
            "../../agents/supervisors/recruiter/oasf/agents/recruiter.json",
        },
        {
          id: ANCHOR,
          type: "customNode",
          label: "Agentic Recruiter",
          layer_index: 0,
        },
        {
          id: DISCOVERED,
          type: "customNode",
          label: "Brazil",
          layer_index: 1,
          stable_agent_id: DISCOVERED_SID,
          oasf_record: record,
          agent_cid: "cidB",
        },
      ],
      edges: [
        {
          id: "edge://discovery-1",
          type: "custom",
          source: ANCHOR,
          target: DISCOVERED,
        },
      ],
    },
    { validateUrls: false },
  )

  it("collapses the anchor onto the single seeded recruiter node", () => {
    const recruiters = nodes.filter(
      (n) => customNodeDataFromNode(n).label === "Agentic",
    )
    expect(recruiters).toHaveLength(1)
    expect(recruiters[0]?.id).toBe(SEED_RECRUITER)
  })

  it("renders the discovered node with inline OASF and a target handle", () => {
    const discovered = nodes.find((n) => n.id === DISCOVERED_SID)
    const data = discovered ? customNodeDataFromNode(discovered) : undefined
    expect(discovered?.type).toBe(NODE_TYPES.CUSTOM)
    expect(data?.oasfRecord).toEqual(record)
    expect(data?.agentCid).toBe("cidB")
    expect(data?.handles).toBe("target")
    expect(data?.agentDirectoryLink).toBeDefined()
  })

  it("re-points the discovered edge from the seeded recruiter to the agent", () => {
    expect(edges).toHaveLength(1)
    expect(edges[0]?.source).toBe(SEED_RECRUITER)
    expect(edges[0]?.target).toBe(DISCOVERED_SID)
  })
})
