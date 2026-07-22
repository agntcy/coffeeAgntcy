/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { customNodeDataFixture } from "@/components/MainArea/Graph/Elements/customNodeData"
import {
  applyBackendTopologyWireFields,
  applyDiscoveredAgentInlineUi,
  directoryAgentSlugFromAgentRecordUri,
  enrichAgenticTopologyWellKnownUi,
  getOasfSlugFromNodeData,
  isDirectoryLabel,
  isMcpServerLabel,
  isRecruiterLabel,
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
    const base = customNodeDataFixture({
      label: "Brazil",
      label_subtitle: "Coffee Farm",
    })
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
    const base = customNodeDataFixture({
      label: "Colombia",
      label_subtitle: "Coffee Farm",
    })
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
      const data = customNodeDataFixture({
        label: "Not",
        label_subtitle: "Logistics Group",
      })
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
      const data = customNodeDataFixture({
        label: "AGNTCY Agent",
        label_subtitle: "Directory",
      })
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
      const data = customNodeDataFixture({
        label: "AGNTCY Agent",
        label_subtitle: "Directory",
      })
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
        data: customNodeDataFixture({
          label: "Agentic Recruiter",
          label_subtitle: "Discovery and delegation",
        }),
        expected: "recruiter",
      },
      {
        caseName: "topology split: Agentic + Recruiter",
        data: customNodeDataFixture({
          label: "Agentic",
          label_subtitle: "Recruiter",
        }),
        expected: "recruiter",
      },
      {
        caseName: "logistics group labels",
        data: customNodeDataFixture({
          label: "Logistics",
          label_subtitle: "Group",
        }),
        expected: "logistics-supervisor-agent",
      },
      {
        caseName: "MCP weather labels (title + role)",
        data: customNodeDataFixture({
          label: "Weather",
          label_subtitle: "MCP Server",
        }),
        expected: "weather-mcp-server",
      },
      {
        caseName: "MCP payment labels (title + role)",
        data: customNodeDataFixture({
          label: "Payment",
          label_subtitle: "MCP Server",
        }),
        expected: "payment-mcp-server",
      },
    ])("$caseName", ({ data, expected }) => {
      expect(getOasfSlugFromNodeData(data)).toBe(expected)
    })

    it("prefers directoryAgentSlug when set", () => {
      expect(
        getOasfSlugFromNodeData(
          customNodeDataFixture({
            label: "Wrong",
            label_subtitle: "Labels",
            directoryAgentSlug: "recruiter",
          }),
        ),
      ).toBe("recruiter")
    })
  })

  describe("applyDiscoveredAgentInlineUi", () => {
    const baseData = customNodeDataFixture({
      label: "Brazil",
    })

    it("returns data unchanged when the wire has no inline OASF record", () => {
      const wire: TopologyNodeWire = { id: "n1" }
      const out = applyDiscoveredAgentInlineUi(baseData, wire)
      expect(out).toBe(baseData)
    })

    it("threads inline OASF record, cid, target handle and directory link", () => {
      const record = { name: "Brazil", url: "http://brazil:9000" }
      const wire: TopologyNodeWire = {
        id: "n1",
        oasf_record: record,
        agent_cid: "cidB",
      }
      const out = applyDiscoveredAgentInlineUi(baseData, wire)
      expect(out.oasfRecord).toEqual(record)
      expect(out.agentCid).toBe("cidB")
      expect(out.handles).toBe("target")
      expect(out.agentDirectoryLink).toBe(
        LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
      )
    })

    it("keeps an existing directory link when already present", () => {
      const wire: TopologyNodeWire = {
        id: "n1",
        oasf_record: { name: "Brazil" },
      }
      const out = applyDiscoveredAgentInlineUi(
        { ...baseData, agentDirectoryLink: "https://example.com/x" },
        wire,
      )
      expect(out.agentDirectoryLink).toBe("https://example.com/x")
    })
  })

  describe("label predicates", () => {
    it.each([
      { caseName: "weather mcp server", label: "Weather MCP Server", v: true },
      {
        caseName: "lowercased mcp server",
        label: "payment mcp server",
        v: true,
      },
      {
        caseName: "trailing whitespace",
        label: "Weather MCP Server  ",
        v: true,
      },
      { caseName: "not at end", label: "MCP Server Gateway", v: false },
      { caseName: "plain agent", label: "Brazil Coffee Farm Agent", v: false },
    ])("isMcpServerLabel: $caseName", ({ label, v }) => {
      expect(isMcpServerLabel(label)).toBe(v)
    })

    it.each([
      { caseName: "agentic recruiter", label: "Agentic Recruiter", v: true },
      {
        caseName: "split labels combined",
        label: "agentic recruiter delegation",
        v: true,
      },
      { caseName: "recruiter alone", label: "Recruiter", v: false },
      { caseName: "directory", label: "AGNTCY Agent Directory", v: false },
    ])("isRecruiterLabel: $caseName", ({ label, v }) => {
      expect(isRecruiterLabel(label)).toBe(v)
    })

    it.each([
      {
        caseName: "agntcy agent directory",
        label: "AGNTCY Agent Directory",
        v: true,
      },
      {
        caseName: "combined labels",
        label: "directory agntcy agent directory",
        v: true,
      },
      { caseName: "missing agntcy", label: "Agent Directory", v: false },
      { caseName: "recruiter", label: "Agentic Recruiter", v: false },
    ])("isDirectoryLabel: $caseName", ({ label, v }) => {
      expect(isDirectoryLabel(label)).toBe(v)
    })
  })
})
