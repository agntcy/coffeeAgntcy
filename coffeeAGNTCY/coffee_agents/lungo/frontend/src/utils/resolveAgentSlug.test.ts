/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { customNodeDataFixture as node } from "@/components/MainArea/Graph/Elements/customNodeData"
import { resolveAgentSlug } from "@/utils/resolveAgentSlug"

describe("resolveAgentSlug", () => {
  it.each([
    {
      caseName: "oasf prefers directoryAgentSlug",
      data: node({
        label: "Wrong",
        label_subtitle: "Labels",
        directoryAgentSlug: "recruiter",
      }),
      purpose: "oasf" as const,
      expected: "recruiter",
    },
    {
      caseName: "identity prefers identityAppsSlug",
      data: node({
        label: "Wrong",
        label_subtitle: "Labels",
        identityAppsSlug: "colombia-coffee-farm",
      }),
      purpose: "identity" as const,
      expected: "colombia-coffee-farm",
    },
    {
      caseName: "shared slug field",
      data: node({
        label: "Ignored",
        label_subtitle: "Labels",
        slug: "shipping-agent",
      }),
      purpose: "oasf" as const,
      expected: "shipping-agent",
    },
    {
      caseName: "auction labels resolve to identity slug",
      data: node({
        label: "Auction Agent",
        label_subtitle: "Buyer",
      }),
      purpose: "identity" as const,
      expected: "auction-supervisor",
    },
    {
      caseName: "auction labels resolve to oasf slug",
      data: node({
        label: "Auction Agent",
        label_subtitle: "Buyer",
      }),
      purpose: "oasf" as const,
      expected: "auction-supervisor-agent",
    },
    {
      caseName: "MCP weather labels",
      data: node({
        label: "Weather",
        label_subtitle: "MCP Server",
      }),
      purpose: "oasf" as const,
      expected: "weather-mcp-server",
    },
    {
      caseName: "identity payment MCP labels",
      data: node({
        label: "MCP Server",
        label_subtitle: "Payment",
      }),
      purpose: "identity" as const,
      expected: "payment-mcp-server",
    },
  ])("$caseName", ({ data, purpose, expected }) => {
    expect(resolveAgentSlug(data, purpose)).toBe(expected)
  })

  it("throws when node data is missing", () => {
    expect(() => resolveAgentSlug(null, "oasf")).toThrow("nodeData is required")
  })

  it("throws when no mapping matches", () => {
    expect(() =>
      resolveAgentSlug(
        node({ label: "Unknown", label_subtitle: "Node" }),
        "oasf",
      ),
    ).toThrow("No valid slug mapping found")
  })
})
