/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * -----------------------------------------------------------------------------
 * Presentation-only icon resolver for dynamically rendered topology nodes.
 *
 * Backend topology carries no icon field, so the dynamic renderer derives a
 * branded icon from a node's directory slug (preferred) or its split label,
 * using loose substring matching rather than an exhaustive agent map. This is
 * presentation, not data: if the backend later supplies an icon/type hint, key
 * off that.
 * -----------------------------------------------------------------------------
 */

import React from "react"
import Air from "@mui/icons-material/Air"
import Calculate from "@mui/icons-material/Calculate"
import LocalShipping from "@mui/icons-material/LocalShipping"
import SmartToy from "@mui/icons-material/SmartToy"
import { GraphDiscoveryAssetImg } from "@/utils/GraphDiscoveryAssetImg"
import {
  isDirectoryLabel,
  isRecruiterLabel,
} from "@/utils/agenticTopologyIdentityUiMap"
import supervisorIcon from "@/assets/supervisor.png"
import farmAgentIcon from "@/assets/Grader-Agent.png"

export interface TopologyNodeIconInput {
  label?: string
  label_subtitle?: string
  directoryAgentSlug?: string
}

export type TopologyNodeIconKind =
  | "supervisor"
  | "recruiter"
  | "directory"
  | "farm"
  | "weatherMcp"
  | "paymentMcp"
  | "shipping"
  | "accountant"
  | "default"

function normalize(value: string | undefined): string {
  return typeof value === "string" ? value.trim().toLowerCase() : ""
}

function iconKindFromSlug(slug: string): TopologyNodeIconKind | null {
  if (slug.includes("supervisor")) return "supervisor"
  if (slug.includes("recruiter")) return "recruiter"
  if (slug.includes("farm")) return "farm"
  if (slug.includes("weather")) return "weatherMcp"
  if (slug.includes("payment")) return "paymentMcp"
  if (slug.includes("shipping")) return "shipping"
  if (slug.includes("accountant")) return "accountant"
  return null
}

function iconKindFromLabels(
  label: string,
  label_subtitle: string,
): TopologyNodeIconKind {
  const combined = `${label} ${label_subtitle}`.trim()

  if (label_subtitle === "mcp server" || label.endsWith("mcp server")) {
    if (label.includes("weather")) return "weatherMcp"
    if (label.includes("payment")) return "paymentMcp"
    return "default"
  }

  if (isRecruiterLabel(combined)) {
    return "recruiter"
  }

  if (label === "directory" || isDirectoryLabel(combined)) {
    return "directory"
  }

  if (label_subtitle.includes("coffee farm")) return "farm"
  if (label === "shipper") return "shipping"
  if (label === "accountant") return "accountant"

  if (
    label === "auction agent" ||
    (label === "auction" && label_subtitle.includes("agent")) ||
    label === "buyer" ||
    label_subtitle.includes("buyer") ||
    label_subtitle.includes("logistics agent") ||
    combined === "logistics group"
  ) {
    return "supervisor"
  }

  return "default"
}

export function topologyNodeIconKind(
  input: TopologyNodeIconInput,
): TopologyNodeIconKind {
  const slug = normalize(input.directoryAgentSlug)
  if (slug) {
    const bySlug = iconKindFromSlug(slug)
    if (bySlug) return bySlug
  }
  return iconKindFromLabels(
    normalize(input.label),
    normalize(input.label_subtitle),
  )
}

function brandedImg(src: string, alt: string): React.ReactNode {
  return <GraphDiscoveryAssetImg src={src} alt={alt} invertInDarkMode />
}

export function resolveTopologyNodeIcon(
  input: TopologyNodeIconInput,
): React.ReactNode {
  switch (topologyNodeIconKind(input)) {
    case "supervisor":
      return brandedImg(supervisorIcon, "Supervisor Icon")
    case "recruiter":
      return brandedImg(supervisorIcon, "Recruiter Icon")
    case "directory":
      return brandedImg(supervisorIcon, "Directory Icon")
    case "farm":
      return brandedImg(farmAgentIcon, "Farm Agent Icon")
    case "weatherMcp":
      return <Air aria-hidden />
    case "paymentMcp":
      return <Calculate aria-hidden />
    case "shipping":
      return <LocalShipping aria-hidden />
    case "accountant":
      return <Calculate aria-hidden />
    default:
      return <SmartToy aria-hidden />
  }
}
