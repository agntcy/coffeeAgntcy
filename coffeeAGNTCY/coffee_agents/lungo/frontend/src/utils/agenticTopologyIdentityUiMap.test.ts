/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import {
  applyBackendTopologyWireFields,
  directoryAgentSlugFromAgentRecordUri,
  enrichAgenticTopologyWellKnownUi,
  getOasfSlugFromNodeData,
  normalizeAgentRecordUriToRepoPath,
  parseStableAgentUuid,
  resolveGithubFromAgentRecordUri,
  stableAgentIdFromWire,
  stableAgentUuidForRecordName,
} from "@/utils/agenticTopologyIdentityUiMap"

/** Must match `uuid5(uuid5(NAMESPACE_DNS, "agent.workflow.lungo"), name)` in Python `common/stable_agent_id.py`. */
const BRAZIL_UUID = "9a6cc736-d6fb-5a3e-82d6-3552d09b5ae9"

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
    const root = LUNGO_FRONTEND_URLS.github.baseUrl.replace(/\/$/, "")
    expect(url).toBe(
      `${root}/lungo/agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json`,
    )
  })

  it.each([
    {
      caseName: "relative path",
      uri: "../../agents/supervisors/auction/oasf/agents/brazil-coffee-farm.json",
      expected: "brazil-coffee-farm",
    },
    {
      caseName: "https raw github path",
      uri: "https://raw.githubusercontent.com/agntcy/coffeeAgntcy/refs/heads/main/coffeeAGNTCY/coffee_agents/lungo/agents/supervisors/recruiter/oasf/agents/recruiter.json",
      expected: "recruiter",
    },
    {
      caseName: "empty",
      uri: "",
      expected: undefined,
    },
  ])("directoryAgentSlugFromAgentRecordUri: $caseName", ({ uri, expected }) => {
    expect(directoryAgentSlugFromAgentRecordUri(uri)).toBe(expected)
  })

  it("applyBackendTopologyWireFields applies enrichment and defaults", () => {
    const base = {
      icon: null,
      label1: "Brazil",
      label2: "Coffee Farm",
      handles: "all",
    } as unknown as CustomNodeData
    const wire: TopologyNodeWire = {
      id: "node://1",
      agent_directory_cid:
        "/baeareigpu5jgm3xrkouspfacgvq65i25cz63nnseqatu5davp35jenwlla",
      has_badge_override: false,
      has_policy_override: false,
      verification_status_override: "failed",
    }
    const merged = applyBackendTopologyWireFields(base, wire, {
      validateUrls: false,
    })
    expect(merged.agentDirectoryLink).toContain(
      "baeareigpu5jgm3xrkouspfacgvq65i25cz63nnseqatu5davp35jenwlla",
    )
    expect(merged.hasBadgeDetails).toBe(false)
    expect(merged.hasPolicyDetails).toBe(false)
    expect(merged.verificationStatus).toBe("failed")
  })

  it("applyBackendTopologyWireFields defaults badge/policy to true when overrides absent", () => {
    const base = {
      icon: null,
      label1: "Colombia",
      label2: "Coffee Farm",
      handles: "all",
    } as unknown as CustomNodeData
    const wire: TopologyNodeWire = {
      id: "node://1",
      identity_app_slug: "colombia-coffee-farm",
    }
    const merged = applyBackendTopologyWireFields(base, wire, {
      validateUrls: false,
    })
    expect(merged.identityAppsSlug).toBe("colombia-coffee-farm")
    expect(merged.hasBadgeDetails).toBe(true)
    expect(merged.hasPolicyDetails).toBe(true)
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

  describe("enrichAgenticTopologyWellKnownUi", () => {
    it("enriches group node by type only", () => {
      const data = {
        icon: null,
        label1: "Not",
        label2: "Logistics Group",
        handles: "all",
      } as unknown as CustomNodeData
      const wire: TopologyNodeWire = {
        id: "g1",
        type: "group",
        label: "Anything",
      }
      const out = enrichAgenticTopologyWellKnownUi(data, wire, {
        validateUrls: false,
      })
      expect(out.directoryAgentSlug).toBe("logistics-supervisor-agent")
      expect(out.githubLink).toContain("transport")
    })

    it("enriches directory node only for customNode + label", () => {
      const data = {
        icon: null,
        label1: "AGNTCY Agent",
        label2: "Directory",
        handles: "all",
      } as unknown as CustomNodeData
      const wire: TopologyNodeWire = {
        id: "d1",
        type: "customNode",
        label: "AGNTCY Agent Directory",
      }
      const out = enrichAgenticTopologyWellKnownUi(data, wire, {
        validateUrls: false,
      })
      expect(out.githubLink).toContain("github.com")
    })

    it("does not enrich directory labels on non-customNode types", () => {
      const data = {
        icon: null,
        label1: "AGNTCY Agent",
        label2: "Directory",
        handles: "all",
      } as unknown as CustomNodeData
      const wire: TopologyNodeWire = {
        id: "d1",
        type: "group",
        label: "AGNTCY Agent Directory",
      }
      const out = enrichAgenticTopologyWellKnownUi(data, wire, {
        validateUrls: false,
      })
      expect(out.githubLink).toContain("transport")
    })
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
      {
        caseName: "MCP weather labels (title + role)",
        data: {
          icon: null,
          label1: "Weather",
          label2: "MCP Server",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "weather-mcp-server",
      },
      {
        caseName: "MCP payment labels (title + role)",
        data: {
          icon: null,
          label1: "Payment",
          label2: "MCP Server",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "payment-mcp-server",
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
