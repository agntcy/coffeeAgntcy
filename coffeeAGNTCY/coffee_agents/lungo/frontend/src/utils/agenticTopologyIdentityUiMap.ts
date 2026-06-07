/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * TEMPORARY: Agentic topology UI enrichment (identity, directory/OASF, GitHub)
 *
 * This map exists only until the backend supplies equivalent fields on workflow
 * topology or catalog API responses (directory URLs, badge flags, identity slugs).
 * `directoryAgentSlug` is derived from topology `agent_record_uri` (record basename).
 * Remove or replace remaining rows when that contract is available.
 * -----------------------------------------------------------------------------
 */

import { v5 as uuidv5 } from "uuid"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { VERIFICATION_STATUS } from "@/utils/const"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"
import urlsConfig from "@/utils/urls.json"
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
  hasBadgeDetails?: boolean
  hasPolicyDetails?: boolean
  agentDirectoryLink: string
  /** Legacy composed URL from static graph (docs / test anchor). */
  referenceGithubUrl: string
  referenceGithubUrlStreaming?: string
  /** When set, overrides default verified-from-topology for identity/badge parity. */
  verificationStatus?: "verified" | "failed"
}

const GITHUB_AGNTCY_BROWSE_ROOT = urlsConfig.github.baseUrl.replace(/\/$/, "")

const RAW_IDENTITY_UI_ROWS: AgenticTopologyIdentityUiRow[] = [
  {
    agentRecordName: "Auction Supervisor agent",
    identityAppsSlug: "auction-supervisor",
    hasBadgeDetails: true,
    hasPolicyDetails: true,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.supervisorAuction}`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.supervisorAuction}`,
    referenceGithubUrlStreaming: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.supervisorAuctionStreaming}`,
  },
  {
    agentRecordName: "Brazil Coffee Farm",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.brazilFarm}`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.brazilFarm}`,
    referenceGithubUrlStreaming: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.brazilFarmStreaming}`,
    verificationStatus: VERIFICATION_STATUS.FAILED,
  },
  {
    agentRecordName: "Colombia Coffee Farm",
    identityAppsSlug: "colombia-coffee-farm",
    hasBadgeDetails: true,
    hasPolicyDetails: true,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.colombiaFarm}`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.colombiaFarm}`,
    referenceGithubUrlStreaming: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.colombiaFarmStreaming}`,
  },
  {
    agentRecordName: "Vietnam Coffee Farm",
    identityAppsSlug: "vietnam-coffee-farm",
    hasBadgeDetails: true,
    hasPolicyDetails: false,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.vietnamFarm}`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.vietnamFarm}`,
    referenceGithubUrlStreaming: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.vietnamFarmStreaming}`,
  },
  {
    agentRecordName: "Weather MCP Server",
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.weatherMcp}`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.weatherMcp}`,
    verificationStatus: VERIFICATION_STATUS.FAILED,
  },
  {
    agentRecordName: "Payment MCP Server",
    identityAppsSlug: "payment-mcp-server",
    hasBadgeDetails: true,
    hasPolicyDetails: false,
    agentDirectoryLink: urlsConfig.agentDirectory.baseUrl,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.paymentMcp}`,
  },
  {
    agentRecordName: "Logistics Supervisor agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: urlsConfig.agentDirectory.baseUrl,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticSupervisor}`,
  },
  {
    agentRecordName: "Tatooine Farm agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticFarm}`,
  },
  {
    agentRecordName: "Shipping agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticShipper}`,
  },
  {
    agentRecordName: "Accountant agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticAccountant}`,
  },
  {
    agentRecordName: "Agentic Recruiter agent",
    hasBadgeDetails: false,
    hasPolicyDetails: false,
    agentDirectoryLink: urlsConfig.agentDirectory.baseUrl,
    referenceGithubUrl: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.recruiter}`,
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

/** Split a topology wire `label` into two lines for `CustomNodeData` (first space). */
export function splitTopologyNodeLabel(label: string): {
  label1: string
  label2: string
} {
  const t = label.trim()
  if (!t) return { label1: "", label2: "" }
  const sp = t.indexOf(" ")
  if (sp === -1) return { label1: t, label2: "" }
  return { label1: t.slice(0, sp), label2: t.slice(sp + 1).trim() }
}

/**
 * Directory / OASF API slug: basename of the OASF record path without `.json`
 * (e.g. `.../brazil-coffee-farm.json` → `brazil-coffee-farm`).
 */
export function directoryAgentSlugFromAgentRecordUri(
  agentRecordUri: string | undefined,
): string | undefined {
  if (!agentRecordUri || typeof agentRecordUri !== "string") return undefined
  const raw = agentRecordUri.trim()
  if (!raw) return undefined

  let pathPart = raw
  if (/^https?:\/\//i.test(raw)) {
    try {
      pathPart = new URL(raw).pathname
    } catch {
      return undefined
    }
  } else {
    pathPart = raw.replace(/\\/g, "/")
  }

  const segments = pathPart.split("/").filter(Boolean)
  if (segments.length === 0) return undefined
  const base = segments[segments.length - 1] ?? ""
  const slug = base.replace(/\.json$/i, "").trim()
  return slug || undefined
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
 * using the same browse root as the legacy static graph (`urlsConfig.github.baseUrl`).
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
  const combined = [data.label1, data.label2].filter(Boolean).join(" ").trim()
  const combinedLower = combined.toLowerCase()

  const safeUrl = (url: string | undefined): string | undefined => {
    if (!url) return undefined
    if (!options.validateUrls || SecurityClass.isSafeExternalUrl(url))
      return url
    return undefined
  }

  if (typeLower === "group" || combinedLower === "logistics group") {
    const transportUrl = `${urlsConfig.github.appSdkBaseUrl}${urlsConfig.github.transports.group}`
    return {
      ...data,
      githubLink: data.githubLink ?? safeUrl(transportUrl),
      agentDirectoryLink:
        data.agentDirectoryLink ?? urlsConfig.agentDirectory.baseUrl,
      directoryAgentSlug:
        data.directoryAgentSlug ?? "logistics-supervisor-agent",
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  const isAgntcyDirectory =
    combinedLower.includes("agntcy") &&
    combinedLower.includes("agent directory")

  if (isAgntcyDirectory) {
    const dirGh = urlsConfig.agentDirectory.github
    return {
      ...data,
      githubLink: data.githubLink ?? safeUrl(dirGh),
      agentDirectoryLink:
        data.agentDirectoryLink ?? urlsConfig.agentDirectory.baseUrl,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  const label1Lower = data.label1?.toLowerCase() ?? ""
  const label2Lower = data.label2?.toLowerCase() ?? ""
  const recruiterLabels = `${label1Lower} ${label2Lower}`.trim()
  if (
    /\bagentic\b/.test(recruiterLabels) &&
    /\brecruiter\b/.test(recruiterLabels) &&
    !data.githubLink
  ) {
    const ref = `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.recruiter}`
    return {
      ...data,
      githubLink: safeUrl(ref),
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
    }
  }

  return data
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

  const directoryAgentSlug =
    data.directoryAgentSlug ??
    directoryAgentSlugFromAgentRecordUri(
      wire.agent_record_uri as string | undefined,
    )

  const merged: CustomNodeData = {
    ...data,
    identityAppsSlug: row.identityAppsSlug,
    ...(directoryAgentSlug ? { directoryAgentSlug } : {}),
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

/**
 * Resolve `GET .../agents/{slug}/oasf` slug from node data.
 * Agentic topology sets `directoryAgentSlug` from `agent_record_uri`; label rules
 * below remain for legacy static graphs without catalog URIs.
 */
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

  const label1 = nodeData.label1?.toLowerCase()
  const label2 = nodeData.label2?.toLowerCase()
  const labelsText = `${label1 ?? ""} ${label2 ?? ""}`.trim()

  if (/\bagentic\b/.test(labelsText) && /\brecruiter\b/.test(labelsText)) {
    return "recruiter"
  }

  if (labelsText === "logistics group") {
    return "logistics-supervisor-agent"
  }

  if (label1 === "auction agent" || label2?.includes("buyer")) {
    return "auction-supervisor-agent"
  }

  if (label1 === "auction" && label2?.includes("agent")) {
    return "auction-supervisor-agent"
  }

  if (label1 === "mcp server" && label2 === "weather") {
    return "weather-mcp-server"
  }

  if (label1 === "colombia" && label2?.includes("coffee farm")) {
    return "colombia-coffee-farm"
  }

  if (label1 === "vietnam" && label2?.includes("coffee farm")) {
    return "vietnam-coffee-farm"
  }

  if (label1 === "brazil" && label2?.includes("coffee farm")) {
    return "brazil-coffee-farm"
  }

  if (label1 === "buyer" || label2?.includes("logistics agent")) {
    return "logistics-supervisor-agent"
  }

  if (label1 === "tatooine" && label2?.includes("coffee farm")) {
    return "tatooine-farm-agent"
  }

  if (label1 === "mcp server" && label2 === "payment") {
    return "payment-mcp-server"
  }

  if (label1 === "shipper") {
    return "shipping-agent"
  }

  if (label1 === "accountant") {
    return "accountant-agent"
  }

  throw new Error(`No valid slug mapping found for node: ${label1} ${label2}`)
}
