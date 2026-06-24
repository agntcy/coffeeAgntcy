/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import {
  applyDiscoveredAgentInlineUi,
  getOasfSlugFromNodeData,
  IDENTITY_UI_BY_STABLE_AGENT_UUID,
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
          label: "Agentic Recruiter",
          label_subtitle: "Discovery and delegation",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "recruiter",
      },
      {
        caseName: "topology split: Agentic + Recruiter",
        data: {
          icon: null,
          label: "Agentic",
          label_subtitle: "Recruiter",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "recruiter",
      },
      {
        caseName: "logistics group labels",
        data: {
          icon: null,
          label: "Logistics",
          label_subtitle: "Group",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "logistics-supervisor-agent",
      },
      {
        caseName: "MCP weather labels (title + role)",
        data: {
          icon: null,
          label: "Weather",
          label_subtitle: "MCP Server",
          handles: "all",
        } as unknown as CustomNodeData,
        expected: "weather-mcp-server",
      },
      {
        caseName: "MCP payment labels (title + role)",
        data: {
          icon: null,
          label: "Payment",
          label_subtitle: "MCP Server",
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
          label: "Wrong",
          label_subtitle: "Labels",
          handles: "all",
          directoryAgentSlug: "recruiter",
        } as unknown as CustomNodeData),
      ).toBe("recruiter")
    })
  })

  describe("applyDiscoveredAgentInlineUi", () => {
    const baseData: CustomNodeData = {
      icon: null,
      label: "Brazil",
      label_subtitle: "",
      handles: "all",
    }

    it("returns data unchanged when the wire has no inline OASF record", () => {
      const out = applyDiscoveredAgentInlineUi(baseData, {
        id: "n1",
      } as TopologyNodeWire)
      expect(out).toBe(baseData)
    })

    it("threads inline OASF record, cid, target handle and directory link", () => {
      const record = { name: "Brazil", url: "http://brazil:9000" }
      const out = applyDiscoveredAgentInlineUi(baseData, {
        id: "n1",
        oasf_record: record,
        agent_cid: "cidB",
      } as unknown as TopologyNodeWire)
      expect(out.oasfRecord).toEqual(record)
      expect(out.agentCid).toBe("cidB")
      expect(out.handles).toBe("target")
      expect(out.agentDirectoryLink).toBe(
        LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
      )
    })

    it("keeps an existing directory link when already present", () => {
      const out = applyDiscoveredAgentInlineUi(
        { ...baseData, agentDirectoryLink: "https://example.com/x" },
        {
          id: "n1",
          oasf_record: { name: "Brazil" },
        } as unknown as TopologyNodeWire,
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
