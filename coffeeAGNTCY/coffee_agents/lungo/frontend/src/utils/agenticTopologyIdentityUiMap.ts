/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * TEMPORARY: Agentic topology UI enrichment (identity, directory/OASF, GitHub)
 *
 * This map exists only until the backend supplies equivalent fields on workflow
 * topology or catalog API responses (stable slugs, directory URLs, badge flags).
 * Remove or replace with API-driven data when that contract is available.
 * -----------------------------------------------------------------------------
 */

import { v5 as uuidv5 } from "uuid"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { HANDLE_TYPES, VERIFICATION_STATUS } from "@/utils/const"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { SecurityClass } from "@/utils/SecurityClass"

/** Matches Python `common.stable_agent_id`: uuid5(NAMESPACE_DNS, "agent.workflow.lungo") */
export const STABLE_AGENT_ID_NAMESPACE = uuidv5(
  "agent.workflow.lungo",
  uuidv5.DNS,
)

export function stableAgentUuidForRecordName(
  agentRecordTopLevelName: string,
): string {
  return uuidv5(agentRecordTopLevelName.trim(), STABLE_AGENT_ID_NAMESPACE)
}

export interface AgenticTopologyIdentityUiRow {
  /** OASF agent card JSON top-level `name` (must match backend record load). */
  agentRecordName: string
  identityAppsSlug?: string
  directoryAgentSlug: string
  hasBadgeDetails?: boolean
  hasPolicyDetails?: boolean
  agentDirectoryLink: string
  /** Legacy composed URL from static graph (docs / test anchor). */
  referenceGithubUrl: string
  referenceGithubUrlStreaming?: string
  /** When set, overrides default verified-from-topology for identity/badge parity. */
  verificationStatus?: "verified" | "failed"
}

const GITHUB_AGNTCY_BROWSE_ROOT = LUNGO_FRONTEND_URLS.github.baseUrl.replace(
  /\/$/,
  "",
)

const RAW_IDENTITY_UI_ROWS: AgenticTopologyIdentityUiRow[] = [
  {
    agentRecordName: "Auction Supervisor agent",
    identityAppsSlug: "auction-supervisor",
    directoryAgentSlug: "auction-supervisor-agent",
    hasBadgeDetails: true,
    hasPolicyDetails: true,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.supervisorAuction}`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.supervisorAuction}`,
    referenceGithubUrlStreaming: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.supervisorAuctionStreaming}`,
  },
  {
    agentRecordName: "Brazil Coffee Farm",
    directoryAgentSlug: "brazil-coffee-farm",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.brazilFarm}`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.brazilFarm}`,
    referenceGithubUrlStreaming: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.brazilFarmStreaming}`,
    verificationStatus: VERIFICATION_STATUS.FAILED,
  },
  {
    agentRecordName: "Colombia Coffee Farm",
    identityAppsSlug: "colombia-coffee-farm",
    directoryAgentSlug: "colombia-coffee-farm",
    hasBadgeDetails: true,
    hasPolicyDetails: true,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.colombiaFarm}`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.colombiaFarm}`,
    referenceGithubUrlStreaming: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.colombiaFarmStreaming}`,
  },
  {
    agentRecordName: "Vietnam Coffee Farm",
    identityAppsSlug: "vietnam-coffee-farm",
    directoryAgentSlug: "vietnam-coffee-farm",
    hasBadgeDetails: true,
    hasPolicyDetails: false,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.vietnamFarm}`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.vietnamFarm}`,
    referenceGithubUrlStreaming: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.vietnamFarmStreaming}`,
  },
  {
    agentRecordName: "Weather MCP Server",
    directoryAgentSlug: "weather-mcp-server",
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.weatherMcp}`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.weatherMcp}`,
    verificationStatus: VERIFICATION_STATUS.FAILED,
  },
  {
    agentRecordName: "Payment MCP Server",
    identityAppsSlug: "payment-mcp-server",
    directoryAgentSlug: "payment-mcp-server",
    hasBadgeDetails: true,
    hasPolicyDetails: false,
    agentDirectoryLink: LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.paymentMcp}`,
  },
  {
    agentRecordName: "Logistics Supervisor agent",
    directoryAgentSlug: "logistics-supervisor-agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticSupervisor}`,
  },
  {
    agentRecordName: "Tatooine Farm agent",
    directoryAgentSlug: "tatooine-farm-agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticFarm}`,
  },
  {
    agentRecordName: "Shipping agent",
    directoryAgentSlug: "shipping-agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticShipper}`,
  },
  {
    agentRecordName: "Accountant agent",
    directoryAgentSlug: "accountant-agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticAccountant}`,
  },
  {
    agentRecordName: "Agentic Recruiter agent",
    directoryAgentSlug: "recruiter",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
    referenceGithubUrl: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.recruiter}`,
  },
]

function buildIdentityUiByStableAgentUuid(): Record<
  string,
  AgenticTopologyIdentityUiRow
> {
  const out: Record<string, AgenticTopologyIdentityUiRow> = {}
  for (const row of RAW_IDENTITY_UI_ROWS) {
    out[stableAgentUuidForRecordName(row.agentRecordName)] = row
  }
  return out
}

export const IDENTITY_UI_BY_STABLE_AGENT_UUID: Record<
  string,
  AgenticTopologyIdentityUiRow
> = buildIdentityUiByStableAgentUuid()

/** Strip `agent://` prefix if present. */
export function parseStableAgentUuid(
  stableAgentId: string | undefined,
): string | null {
  if (!stableAgentId || typeof stableAgentId !== "string") return null
  const t = stableAgentId.trim()
  if (!t) return null
  return t.replace(/^agent:\/\//i, "")
}

/** Read stable agent id from API wire (string or Pydantic RootModel `{ root }`). */
export function stableAgentIdFromWire(
  wire: TopologyNodeWire,
): string | undefined {
  const raw = wire.stable_agent_id
  if (typeof raw === "string" && raw.trim()) return raw.trim()
  if (raw && typeof raw === "object" && "root" in raw) {
    const r = (raw as { root: unknown }).root
    if (typeof r === "string" && r.trim()) return r.trim()
  }
  return undefined
}

/** Split a single wire `label` into display title and subtitle when no `label_subtitle` is set. */
export function splitTopologyNodeLabel(wireLabel: string): {
  label: string
  label_subtitle: string
} {
  const t = wireLabel.trim()
  if (!t) return { label: "", label_subtitle: "" }

  const mcpSuffix = t.match(/^(.+?)\s+MCP\s+Server$/i)
  if (mcpSuffix) {
    return { label: mcpSuffix[1].trim(), label_subtitle: "MCP Server" }
  }

  const mcpPrefix = t.match(/^MCP\s+Server\s+(.+)$/i)
  if (mcpPrefix) {
    return { label: mcpPrefix[1].trim(), label_subtitle: "MCP Server" }
  }

  const sp = t.indexOf(" ")
  if (sp === -1) return { label: t, label_subtitle: "" }
  return { label: t.slice(0, sp), label_subtitle: t.slice(sp + 1).trim() }
}

/** True when a node label denotes an MCP server (e.g. "Weather MCP Server"). */
export function isMcpServerLabel(label: string): boolean {
  return /mcp\s+server$/i.test(label.trim())
}

/** True when a node label denotes the agentic recruiter. */
export function isRecruiterLabel(label: string): boolean {
  const lower = label.toLowerCase()
  return /\bagentic\b/.test(lower) && /\brecruiter\b/.test(lower)
}

/** True when a node label denotes the AGNTCY agent directory. */
export function isDirectoryLabel(label: string): boolean {
  const lower = label.toLowerCase()
  return lower.includes("agntcy") && lower.includes("agent directory")
}

/**
 * Normalize catalog `agent_record_uri` relative paths to a repo path segment
 * under `coffeeAGNTCY/coffee_agents` (for GitHub blob URLs).
 */
export function normalizeAgentRecordUriToRepoPath(
  agentRecordUri: string,
): string | null {
  let u = agentRecordUri.trim()
  if (!u) return null
  if (/^https?:\/\//i.test(u)) return null
  u = u.replace(/\\/g, "/")
  while (u.startsWith("../") || u.startsWith("./")) {
    if (u.startsWith("./")) u = u.slice(2)
    else if (u.startsWith("../")) u = u.slice(3)
  }
  if (u.startsWith("agents/")) return `lungo/${u}`
  if (u.startsWith("lungo/")) return u
  return null
}

export type IdentityUiGithubVariant =
  | "publish_subscribe"
  | "publish_subscribe_streaming"
  | undefined

/** Maps Lungo catalog pattern to GitHub display variant for stable-agent rows. */
export function identityUiVariantForPattern(
  p: PatternType,
): IdentityUiGithubVariant | undefined {
  if (p === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
    return "publish_subscribe_streaming"
  }
  if (p === PATTERNS.PUBLISH_SUBSCRIBE) {
    return "publish_subscribe"
  }
  return undefined
}

/**
 * Build a browse-safe GitHub URL for the OASF record file from `agent_record_uri`,
 * using the same browse root as the legacy static graph (`LUNGO_FRONTEND_URLS.github.baseUrl`).
 */
export function resolveGithubFromAgentRecordUri(
  agentRecordUri: string | undefined,
  options: { validateUrls: boolean },
): string | undefined {
  if (!agentRecordUri || typeof agentRecordUri !== "string") return undefined
  const raw = agentRecordUri.trim()
  if (!raw) return undefined
  if (/^https?:\/\//i.test(raw)) {
    if (!options.validateUrls || SecurityClass.isSafeExternalUrl(raw))
      return raw
    return undefined
  }
  const rel = normalizeAgentRecordUriToRepoPath(raw)
  if (!rel) return undefined
  const path = rel.replace(/^\/+/, "")
  const url = `${GITHUB_AGNTCY_BROWSE_ROOT}/${path}`
  if (!options.validateUrls || SecurityClass.isSafeExternalUrl(url)) return url
  return undefined
}

/** Label / type fallbacks for catalog workflows until the API supplies these fields. */
export function enrichAgenticTopologyWellKnownUi(
  data: CustomNodeData,
  wire: TopologyNodeWire,
  options: { validateUrls: boolean },
): CustomNodeData {
  const typeLower = typeof wire.type === "string" ? wire.type.toLowerCase() : ""
  const combined = [data.label, data.label_subtitle]
    .filter(Boolean)
    .join(" ")
    .trim()
  const combinedLower = combined.toLowerCase()

  const safeUrl = (url: string | undefined): string | undefined => {
    if (!url) return undefined
    if (!options.validateUrls || SecurityClass.isSafeExternalUrl(url))
      return url
    return undefined
  }

  if (typeLower === "group" || combinedLower === "logistics group") {
    const transportUrl = `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.group}`
    return {
      ...data,
      githubLink: data.githubLink ?? safeUrl(transportUrl),
      agentDirectoryLink:
        data.agentDirectoryLink ?? LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
      directoryAgentSlug:
        data.directoryAgentSlug ?? "logistics-supervisor-agent",
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  const isAgntcyDirectory =
    combinedLower.includes("agntcy") &&
    combinedLower.includes("agent directory")

  if (isAgntcyDirectory) {
    const dirGh = LUNGO_FRONTEND_URLS.agentDirectory.github
    return {
      ...data,
      githubLink: data.githubLink ?? safeUrl(dirGh),
      agentDirectoryLink:
        data.agentDirectoryLink ?? LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  const labelLower = data.label?.toLowerCase() ?? ""
  const labelSubtitleLower = data.label_subtitle?.toLowerCase() ?? ""
  const recruiterLabels = `${labelLower} ${labelSubtitleLower}`.trim()
  if (
    /\bagentic\b/.test(recruiterLabels) &&
    /\brecruiter\b/.test(recruiterLabels) &&
    !data.githubLink
  ) {
    const ref = `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.recruiter}`
    return {
      ...data,
      githubLink: safeUrl(ref),
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  return data
}

/**
 * Apply inline UI for runtime-discovered agents. The recruiter emits the full
 * OASF record (and CID) on the wire node, so the OASF modal reads it directly
 * instead of resolving a static directory slug. Discovered agents are leaf
 * targets of the recruiter edge, so they expose a target handle only.
 */
export function applyDiscoveredAgentInlineUi(
  data: CustomNodeData,
  wire: TopologyNodeWire,
): CustomNodeData {
  const record = wire.oasf_record
  if (!record || typeof record !== "object") return data
  const cid = typeof wire.agent_cid === "string" ? wire.agent_cid : undefined
  return {
    ...data,
    oasfRecord: record as Record<string, unknown>,
    agentCid: cid,
    handles: HANDLE_TYPES.TARGET,
    agentDirectoryLink:
      data.agentDirectoryLink ?? LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
  }
}

/**
 * Merge map + resolved GitHub into agentic `CustomNodeData`. Does not set legacy `slug`
 * (use `identityAppsSlug` / `directoryAgentSlug` on node data).
 */
export function mergeAgenticTopologyIdentityUi(
  data: CustomNodeData,
  wire: TopologyNodeWire,
  options: {
    validateUrls: boolean
    identityUiVariant?: IdentityUiGithubVariant
  },
): CustomNodeData {
  const uuid = parseStableAgentUuid(stableAgentIdFromWire(wire))
  if (!uuid) return data
  const row = IDENTITY_UI_BY_STABLE_AGENT_UUID[uuid]
  if (!row) return data

  const ghFromUri = resolveGithubFromAgentRecordUri(
    wire.agent_record_uri as string | undefined,
    { validateUrls: options.validateUrls },
  )
  const githubStreaming =
    options.identityUiVariant === "publish_subscribe_streaming" &&
    row.referenceGithubUrlStreaming
      ? row.referenceGithubUrlStreaming
      : undefined
  const githubResolved =
    githubStreaming &&
    (!options.validateUrls || SecurityClass.isSafeExternalUrl(githubStreaming))
      ? githubStreaming
      : (ghFromUri ?? data.githubLink)

  const merged: CustomNodeData = {
    ...data,
    identityAppsSlug: row.identityAppsSlug,
    directoryAgentSlug: row.directoryAgentSlug,
    agentDirectoryLink: row.agentDirectoryLink,
    hasBadgeDetails: row.hasBadgeDetails,
    hasPolicyDetails: row.hasPolicyDetails,
    githubLink: githubResolved,
  }
  if (row.verificationStatus !== undefined) {
    merged.verificationStatus = row.verificationStatus
  }
  return merged
}

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

/** Resolve `GET .../agents/{slug}/oasf` slug from merged or static graph node data. */
export function getOasfSlugFromNodeData(
  nodeData: CustomNodeData | null | undefined,
): string {
  if (!nodeData) {
    throw new Error("nodeData is required for slug resolution")
  }
  if (nodeData.directoryAgentSlug) {
    return nodeData.directoryAgentSlug
  }

  if (nodeData.slug) {
    return nodeData.slug
  }

  const label = nodeData.label?.toLowerCase()
  const label_subtitle = nodeData.label_subtitle?.toLowerCase()
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
    return "auction-supervisor-agent"
  }

  if (label === "auction" && label_subtitle?.includes("agent")) {
    return "auction-supervisor-agent"
  }

  if (label === "colombia" && label_subtitle?.includes("coffee farm")) {
    return "colombia-coffee-farm"
  }

  if (label === "vietnam" && label_subtitle?.includes("coffee farm")) {
    return "vietnam-coffee-farm"
  }

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

  throw new Error(
    `No valid slug mapping found for node: ${label} ${label_subtitle}`,
  )
}
