/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { isValidElement } from "react"
import { describe, expect, it } from "vitest"
import {
  resolveTopologyNodeIcon,
  topologyNodeIconKind,
  TopologyNodeIconKind,
  type TopologyNodeIconInput,
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
      expected: TopologyNodeIconKind.Supervisor,
    },
    {
      caseName: "logistics supervisor slug -> supervisor",
      input: { directoryAgentSlug: "logistics-supervisor-agent" },
      expected: TopologyNodeIconKind.Supervisor,
    },
    {
      caseName: "recruiter slug -> recruiter",
      input: { directoryAgentSlug: "recruiter" },
      expected: TopologyNodeIconKind.Recruiter,
    },
    {
      caseName: "coffee farm slug -> farm",
      input: { directoryAgentSlug: "colombia-coffee-farm" },
      expected: TopologyNodeIconKind.Farm,
    },
    {
      caseName: "tatooine farm slug -> farm",
      input: { directoryAgentSlug: "tatooine-farm-agent" },
      expected: TopologyNodeIconKind.Farm,
    },
    {
      caseName: "weather mcp slug -> weatherMcp",
      input: { directoryAgentSlug: "weather-mcp-server" },
      expected: TopologyNodeIconKind.WeatherMcp,
    },
    {
      caseName: "payment mcp slug -> paymentMcp",
      input: { directoryAgentSlug: "payment-mcp-server" },
      expected: TopologyNodeIconKind.PaymentMcp,
    },
    {
      caseName: "shipping slug -> shipping",
      input: { directoryAgentSlug: "shipping-agent" },
      expected: TopologyNodeIconKind.Shipping,
    },
    {
      caseName: "accountant slug -> accountant",
      input: { directoryAgentSlug: "accountant-agent" },
      expected: TopologyNodeIconKind.Accountant,
    },
    {
      caseName: "unknown slug falls back to labels",
      input: { directoryAgentSlug: "mystery", label: "Shipper" },
      expected: TopologyNodeIconKind.Shipping,
    },
    {
      caseName: "weather mcp by labels",
      input: { label: "Weather", label_subtitle: "MCP Server" },
      expected: TopologyNodeIconKind.WeatherMcp,
    },
    {
      caseName: "payment mcp by labels",
      input: { label: "Payment", label_subtitle: "MCP Server" },
      expected: TopologyNodeIconKind.PaymentMcp,
    },
    {
      caseName: "generic mcp by labels -> default",
      input: { label: "Inventory", label_subtitle: "MCP Server" },
      expected: TopologyNodeIconKind.Default,
    },
    {
      caseName: "agentic recruiter by labels",
      input: {
        label: "Agentic Recruiter",
        label_subtitle: "Discovery and delegation",
      },
      expected: TopologyNodeIconKind.Recruiter,
    },
    {
      caseName: "agntcy agent directory by labels",
      input: { label: "Directory", label_subtitle: "AGNTCY Agent Directory" },
      expected: TopologyNodeIconKind.Directory,
    },
    {
      caseName: "coffee farm by labels",
      input: { label: "Brazil", label_subtitle: "Coffee Farm Agent" },
      expected: TopologyNodeIconKind.Farm,
    },
    {
      caseName: "auction agent by labels",
      input: { label: "Auction Agent", label_subtitle: "Buyer" },
      expected: TopologyNodeIconKind.Supervisor,
    },
    {
      caseName: "logistics buyer by labels",
      input: { label: "Buyer", label_subtitle: "Logistics Agent" },
      expected: TopologyNodeIconKind.Supervisor,
    },
    {
      caseName: "shipper by labels",
      input: { label: "Shipper", label_subtitle: "Shipper Agent" },
      expected: TopologyNodeIconKind.Shipping,
    },
    {
      caseName: "accountant by labels",
      input: { label: "Accountant", label_subtitle: "Accountant Agent" },
      expected: TopologyNodeIconKind.Accountant,
    },
    {
      caseName: "unknown -> default",
      input: { label: "Mystery", label_subtitle: "Thing" },
      expected: TopologyNodeIconKind.Default,
    },
    {
      caseName: "empty input -> default",
      input: {},
      expected: TopologyNodeIconKind.Default,
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
