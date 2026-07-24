/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Agentic topology UI enrichment: wire fields from backend OASF annotations,
 * GitHub from `agent_record_uri`, and label/type fallbacks for special nodes.
 */

import { v5 as uuidv5 } from "uuid"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import type { TopologyNodeWire } from "@/api/agenticWorkflowsTypes"
import { HANDLE_TYPES, VERIFICATION_STATUS } from "@/utils/const"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { SecurityClass } from "@/utils/SecurityClass"
import { resolveAgentSlug } from "@/utils/resolveAgentSlug"

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

const GITHUB_AGNTCY_BROWSE_ROOT = LUNGO_FRONTEND_URLS.github.baseUrl.replace(
  /\/$/,
  "",
)

const wireHasOwn = (wire: TopologyNodeWire, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(wire, key)

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
      hasBadgeDetails: false,
      hasPolicyDetails: false,
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
 * Apply inline UI for runtime-discovered agents. The recruiter emits the flat
 * agent record (and CID) on the wire ``oasf_record`` field, so the directory
 * modal reads it directly instead of resolving a static directory slug.
 * Discovered agents are leaf targets of the recruiter edge, so they expose a
 * target handle only.
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
 * Map backend-enriched topology wire fields onto `CustomNodeData`.
 * Does not re-parse OASF or agent URIs; those belong on the wire from the API.
 */
export function applyBackendTopologyWireFields(
  data: CustomNodeData,
  wire: TopologyNodeWire,
  options: { validateUrls: boolean },
): CustomNodeData {
  const merged: CustomNodeData = { ...data }

  const cid = wire.agent_directory_cid
  if (typeof cid === "string" && cid.trim()) {
    const path = cid.startsWith("/") ? cid : `/${cid}`
    const link = `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${path}`
    if (!options.validateUrls || SecurityClass.isSafeExternalUrl(link)) {
      merged.agentDirectoryLink = link
    }
  }

  const identitySlug = wire.identity_app_slug
  if (typeof identitySlug === "string" && identitySlug.trim()) {
    merged.identityAppsSlug = identitySlug.trim()
  }

  if (wireHasOwn(wire, "has_badge_override")) {
    merged.hasBadgeDetails = Boolean(wire.has_badge_override)
  } else {
    merged.hasBadgeDetails = true
  }

  if (wireHasOwn(wire, "has_policy_override")) {
    merged.hasPolicyDetails = Boolean(wire.has_policy_override)
  } else {
    merged.hasPolicyDetails = true
  }

  const verification = wire.verification_status_override
  if (verification === "verified" || verification === "failed") {
    merged.verificationStatus = verification
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
  return resolveAgentSlug(nodeData, "oasf")
}
