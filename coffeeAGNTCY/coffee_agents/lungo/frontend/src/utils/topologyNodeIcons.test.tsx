/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { isValidElement } from "react"
import { describe, expect, it } from "vitest"
import {
  resolveTopologyNodeIcon,
  topologyNodeIconKind,
  type TopologyNodeIconInput,
  type TopologyNodeIconKind,
} from "@/utils/topologyNodeIcons"

describe("topologyNodeIconKind", () => {
  it.each<{
    caseName: string
    input: TopologyNodeIconInput
    expected: TopologyNodeIconKind
  }>([
    {
      caseName: "slug wins over labels (auction supervisor)",
      input: {
        directoryAgentSlug: "auction-supervisor-agent",
        label: "Weather",
        label_subtitle: "MCP Server",
      },
      expected: "supervisor",
    },
    {
      caseName: "logistics supervisor slug -> supervisor",
      input: { directoryAgentSlug: "logistics-supervisor-agent" },
      expected: "supervisor",
    },
    {
      caseName: "recruiter slug -> recruiter",
      input: { directoryAgentSlug: "recruiter" },
      expected: "recruiter",
    },
    {
      caseName: "coffee farm slug -> farm",
      input: { directoryAgentSlug: "colombia-coffee-farm" },
      expected: "farm",
    },
    {
      caseName: "tatooine farm slug -> farm",
      input: { directoryAgentSlug: "tatooine-farm-agent" },
      expected: "farm",
    },
    {
      caseName: "weather mcp slug -> weatherMcp",
      input: { directoryAgentSlug: "weather-mcp-server" },
      expected: "weatherMcp",
    },
    {
      caseName: "payment mcp slug -> paymentMcp",
      input: { directoryAgentSlug: "payment-mcp-server" },
      expected: "paymentMcp",
    },
    {
      caseName: "shipping slug -> shipping",
      input: { directoryAgentSlug: "shipping-agent" },
      expected: "shipping",
    },
    {
      caseName: "accountant slug -> accountant",
      input: { directoryAgentSlug: "accountant-agent" },
      expected: "accountant",
    },
    {
      caseName: "unknown slug falls back to labels",
      input: { directoryAgentSlug: "mystery", label: "Shipper" },
      expected: "shipping",
    },
    {
      caseName: "weather mcp by labels",
      input: { label: "Weather", label_subtitle: "MCP Server" },
      expected: "weatherMcp",
    },
    {
      caseName: "payment mcp by labels",
      input: { label: "Payment", label_subtitle: "MCP Server" },
      expected: "paymentMcp",
    },
    {
      caseName: "generic mcp by labels -> default",
      input: { label: "Inventory", label_subtitle: "MCP Server" },
      expected: "default",
    },
    {
      caseName: "agentic recruiter by labels",
      input: {
        label: "Agentic Recruiter",
        label_subtitle: "Discovery and delegation",
      },
      expected: "recruiter",
    },
    {
      caseName: "agntcy agent directory by labels",
      input: { label: "Directory", label_subtitle: "AGNTCY Agent Directory" },
      expected: "directory",
    },
    {
      caseName: "coffee farm by labels",
      input: { label: "Brazil", label_subtitle: "Coffee Farm Agent" },
      expected: "farm",
    },
    {
      caseName: "auction agent by labels",
      input: { label: "Auction Agent", label_subtitle: "Buyer" },
      expected: "supervisor",
    },
    {
      caseName: "logistics buyer by labels",
      input: { label: "Buyer", label_subtitle: "Logistics Agent" },
      expected: "supervisor",
    },
    {
      caseName: "shipper by labels",
      input: { label: "Shipper", label_subtitle: "Shipper Agent" },
      expected: "shipping",
    },
    {
      caseName: "accountant by labels",
      input: { label: "Accountant", label_subtitle: "Accountant Agent" },
      expected: "accountant",
    },
    {
      caseName: "unknown -> default",
      input: { label: "Mystery", label_subtitle: "Thing" },
      expected: "default",
    },
    {
      caseName: "empty input -> default",
      input: {},
      expected: "default",
    },
  ])("$caseName", ({ input, expected }) => {
    expect(topologyNodeIconKind(input)).toBe(expected)
  })
})

describe("resolveTopologyNodeIcon", () => {
  it("returns a renderable element for every input", () => {
    expect(isValidElement(resolveTopologyNodeIcon({ label: "Shipper" }))).toBe(
      true,
    )
    expect(isValidElement(resolveTopologyNodeIcon({}))).toBe(true)
  })
})
