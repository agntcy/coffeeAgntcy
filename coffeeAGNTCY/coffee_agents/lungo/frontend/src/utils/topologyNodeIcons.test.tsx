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
        label1: "Weather",
        label2: "MCP Server",
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
      input: { directoryAgentSlug: "mystery", label1: "Shipper" },
      expected: "shipping",
    },
    {
      caseName: "weather mcp by labels",
      input: { label1: "Weather", label2: "MCP Server" },
      expected: "weatherMcp",
    },
    {
      caseName: "payment mcp by labels",
      input: { label1: "Payment", label2: "MCP Server" },
      expected: "paymentMcp",
    },
    {
      caseName: "generic mcp by labels -> default",
      input: { label1: "Inventory", label2: "MCP Server" },
      expected: "default",
    },
    {
      caseName: "agentic recruiter by labels",
      input: {
        label1: "Agentic Recruiter",
        label2: "Discovery and delegation",
      },
      expected: "recruiter",
    },
    {
      caseName: "agntcy agent directory by labels",
      input: { label1: "Directory", label2: "AGNTCY Agent Directory" },
      expected: "directory",
    },
    {
      caseName: "coffee farm by labels",
      input: { label1: "Brazil", label2: "Coffee Farm Agent" },
      expected: "farm",
    },
    {
      caseName: "auction agent by labels",
      input: { label1: "Auction Agent", label2: "Buyer" },
      expected: "supervisor",
    },
    {
      caseName: "logistics buyer by labels",
      input: { label1: "Buyer", label2: "Logistics Agent" },
      expected: "supervisor",
    },
    {
      caseName: "shipper by labels",
      input: { label1: "Shipper", label2: "Shipper Agent" },
      expected: "shipping",
    },
    {
      caseName: "accountant by labels",
      input: { label1: "Accountant", label2: "Accountant Agent" },
      expected: "accountant",
    },
    {
      caseName: "unknown -> default",
      input: { label1: "Mystery", label2: "Thing" },
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
    expect(isValidElement(resolveTopologyNodeIcon({ label1: "Shipper" }))).toBe(
      true,
    )
    expect(isValidElement(resolveTopologyNodeIcon({}))).toBe(true)
  })
})
