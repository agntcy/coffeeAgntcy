/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import urlsConfig from "@/utils/urls.json"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import {
  getOasfSlugFromNodeData,
  IDENTITY_UI_BY_STABLE_AGENT_UUID,
  normalizeAgentRecordUriToRepoPath,
  parseStableAgentUuid,
  resolveGithubFromAgentRecordUri,
  stableAgentIdFromWire,
  stableAgentUuidForRecordName,
} from "@/utils/agenticTopologyIdentityUiMap"

/** Must match `uuid5(uuid5(NAMESPACE_DNS, "agent.workflow.lungo.coffeeAGNTCY.com"), name)` in Python `workflows.py`. */
const BRAZIL_UUID = "ea3ce2b8-68b6-5fc9-9fa4-491cb71b7bf4"

describe("agenticTopologyIdentityUiMap", () => {
  it("stableAgentUuidForRecordName matches Python backend for Brazil Coffee Farm", () => {
    expect(stableAgentUuidForRecordName("Brazil Coffee Farm")).toBe(BRAZIL_UUID)
  })

  it.each([
    {
      caseName: "relative catalog uri maps under lungo/agents",
      uri: "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
      expected:
        "lungo/agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
    },
    {
      caseName: "https uri returns null for path normalizer",
      uri: "https://example.com/x.json",
      expected: null,
    },
  ])("$caseName", ({ uri, expected }) => {
    expect(normalizeAgentRecordUriToRepoPath(uri)).toBe(expected)
  })

  it("resolveGithubFromAgentRecordUri joins browse root and normalized path", () => {
    const url = resolveGithubFromAgentRecordUri(
      "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
      { validateUrls: false },
    )
    const root = urlsConfig.github.baseUrl.replace(/\/$/, "")
    expect(url).toBe(
      `${root}/lungo/agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json`,
    )
  })

  it("Brazil row exists in map and includes directory slug and link", () => {
    const row = IDENTITY_UI_BY_STABLE_AGENT_UUID[BRAZIL_UUID]
    expect(row).toBeDefined()
    expect(row?.directoryAgentSlug).toBe("brazil-coffee-farm")
    expect(row?.agentDirectoryLink).toContain("agent-directory")
    expect(row?.identityAppsSlug).toBeUndefined()
  })

  it("parseStableAgentUuid strips agent scheme", () => {
    expect(parseStableAgentUuid(`agent://${BRAZIL_UUID}`)).toBe(BRAZIL_UUID)
  })

  it.each([
    {
      caseName: "stable_agent_id string",
      wire: { id: "n1", stable_agent_id: `agent://${BRAZIL_UUID}` },
      expected: `agent://${BRAZIL_UUID}`,
    },
    {
      caseName: "stable_agent_id RootModel object",
      wire: { id: "n1", stable_agent_id: { root: `agent://${BRAZIL_UUID}` } },
      expected: `agent://${BRAZIL_UUID}`,
    },
  ])("stableAgentIdFromWire: $caseName", ({ wire, expected }) => {
    expect(stableAgentIdFromWire(wire as TopologyNodeWire)).toBe(expected)
  })

  it("logistics and recruiter rows exist in stable-agent map", () => {
    const logisticsUuid = stableAgentUuidForRecordName(
      "Logistics Supervisor agent",
    )
    const recruiterUuid = stableAgentUuidForRecordName(
      "Agentic Recruiter agent",
    )
    expect(
      IDENTITY_UI_BY_STABLE_AGENT_UUID[logisticsUuid]?.directoryAgentSlug,
    ).toBe("logistics-supervisor-agent")
    expect(
      IDENTITY_UI_BY_STABLE_AGENT_UUID[recruiterUuid]?.directoryAgentSlug,
    ).toBe("recruiter")
  })

  describe("getOasfSlugFromNodeData", () => {
    it.each([
      {
        caseName: "static discovery: Agentic Recruiter + subtitle",
        data: {
          icon: null,
          label1: "Agentic Recruiter",
          label2: "Discovery and delegation",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "recruiter",
      },
      {
        caseName: "topology split: Agentic + Recruiter",
        data: {
          icon: null,
          label1: "Agentic",
          label2: "Recruiter",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "recruiter",
      },
      {
        caseName: "logistics group labels",
        data: {
          icon: null,
          label1: "Logistics",
          label2: "Group",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "logistics-supervisor-agent",
      },
    ])("$caseName", ({ data, expected }) => {
      expect(getOasfSlugFromNodeData(data)).toBe(expected)
    })

    it("prefers directoryAgentSlug when set", () => {
      expect(
        getOasfSlugFromNodeData({
          icon: null,
          label1: "Wrong",
          label2: "Labels",
          handles: "all",
          directoryAgentSlug: "recruiter",
        } as unknown as CustomNodeData),
      ).toBe("recruiter")
    })
  })
})
