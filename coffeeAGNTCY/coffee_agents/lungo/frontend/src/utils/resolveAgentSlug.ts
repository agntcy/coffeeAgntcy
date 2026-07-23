/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Resolve agent API slugs from node data (wire-first fields, then label heuristics).
 */

import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

export type AgentSlugPurpose = "oasf" | "identity"

function mcpDirectorySlugFromLabels(
  label: string | undefined,
  label_subtitle: string | undefined,
): string | null {
  const pair = new Set(
    [label, label_subtitle]
      .filter(Boolean)
      .map((part) => part!.trim().toLowerCase()),
  )
  if (pair.has("weather") && pair.has("mcp server")) {
    return "weather-mcp-server"
  }
  if (pair.has("payment") && pair.has("mcp server")) {
    return "payment-mcp-server"
  }
  return null
}

function slugFromLabels(
  label: string | undefined,
  label_subtitle: string | undefined,
  purpose: AgentSlugPurpose,
): string | null {
  const labelsText = `${label ?? ""} ${label_subtitle ?? ""}`.trim()

  const mcpSlug = mcpDirectorySlugFromLabels(label, label_subtitle)
  if (mcpSlug) return mcpSlug

  if (/\bagentic\b/.test(labelsText) && /\brecruiter\b/.test(labelsText)) {
    return "recruiter"
  }

  if (labelsText === "logistics group") {
    return "logistics-supervisor-agent"
  }

  if (label === "auction agent" || label_subtitle?.includes("buyer")) {
    return purpose === "identity"
      ? "auction-supervisor"
      : "auction-supervisor-agent"
  }

  if (label === "auction" && label_subtitle?.includes("agent")) {
    return purpose === "identity"
      ? "auction-supervisor"
      : "auction-supervisor-agent"
  }

  if (label === "colombia" && label_subtitle?.includes("coffee farm")) {
    return "colombia-coffee-farm"
  }

  if (label === "vietnam" && label_subtitle?.includes("coffee farm")) {
    return "vietnam-coffee-farm"
  }

  if (purpose === "oasf") {
    if (label === "brazil" && label_subtitle?.includes("coffee farm")) {
      return "brazil-coffee-farm"
    }
    if (label === "buyer" || label_subtitle?.includes("logistics agent")) {
      return "logistics-supervisor-agent"
    }
    if (label === "tatooine" && label_subtitle?.includes("coffee farm")) {
      return "tatooine-farm-agent"
    }
    if (label === "shipper") {
      return "shipping-agent"
    }
    if (label === "accountant") {
      return "accountant-agent"
    }
  }

  if (purpose === "identity") {
    if (label === "mcp server" && label_subtitle === "payment") {
      return "payment-mcp-server"
    }
  }

  return null
}

/**
 * Resolve slug for OASF directory or identity-apps APIs.
 * Prefers wire-populated fields on `CustomNodeData` before label heuristics.
 */
export function resolveAgentSlug(
  nodeData: CustomNodeData | null | undefined,
  purpose: AgentSlugPurpose,
): string {
  if (!nodeData) {
    throw new Error("nodeData is required for slug resolution")
  }

  if (purpose === "identity" && nodeData.identityAppsSlug) {
    return nodeData.identityAppsSlug
  }

  if (purpose === "oasf" && nodeData.directoryAgentSlug) {
    return nodeData.directoryAgentSlug
  }

  if (nodeData.slug) {
    return nodeData.slug
  }

  const label = nodeData.label?.toLowerCase()
  const label_subtitle = nodeData.label_subtitle?.toLowerCase()
  const fromLabels = slugFromLabels(label, label_subtitle, purpose)
  if (fromLabels) return fromLabels

  throw new Error(
    `No valid slug mapping found for node: ${label} ${label_subtitle}`,
  )
}
