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
  label1?: string
  label2?: string
  directoryAgentSlug?: string
}

export enum TopologyNodeIconKind {
  Supervisor = "supervisor",
  Recruiter = "recruiter",
  Directory = "directory",
  Farm = "farm",
  WeatherMcp = "weatherMcp",
  PaymentMcp = "paymentMcp",
  Shipping = "shipping",
  Accountant = "accountant",
  Default = "default",
}

function normalize(value: string | undefined): string {
  return typeof value === "string" ? value.trim().toLowerCase() : ""
}

function iconKindFromSlug(slug: string): TopologyNodeIconKind | null {
  if (slug.includes(TopologyNodeIconKind.Supervisor)) {
    return TopologyNodeIconKind.Supervisor
  }
  if (slug.includes(TopologyNodeIconKind.Recruiter)) {
    return TopologyNodeIconKind.Recruiter
  }
  if (slug.includes(TopologyNodeIconKind.Farm)) {
    return TopologyNodeIconKind.Farm
  }
  if (slug.includes("weather")) {
    return TopologyNodeIconKind.WeatherMcp
  }
  if (slug.includes("payment")) {
    return TopologyNodeIconKind.PaymentMcp
  }
  if (slug.includes(TopologyNodeIconKind.Shipping)) {
    return TopologyNodeIconKind.Shipping
  }
  if (slug.includes(TopologyNodeIconKind.Accountant)) {
    return TopologyNodeIconKind.Accountant
  }
  return null
}

function iconKindFromLabels(
  label1: string,
  label2: string,
): TopologyNodeIconKind {
  const combined = `${label1} ${label2}`.trim()

  if (label2 === "mcp server" || label1.endsWith("mcp server")) {
    if (label1.includes("weather")) return TopologyNodeIconKind.WeatherMcp
    if (label1.includes("payment")) return TopologyNodeIconKind.PaymentMcp
    return TopologyNodeIconKind.Default
  }

  if (isRecruiterLabel(combined)) {
    return TopologyNodeIconKind.Recruiter
  }

  if (label1 === "directory" || isDirectoryLabel(combined)) {
    return TopologyNodeIconKind.Directory
  }

  if (label2.includes("coffee farm")) return TopologyNodeIconKind.Farm
  if (label1 === "shipper") return TopologyNodeIconKind.Shipping
  if (label1 === "accountant") return TopologyNodeIconKind.Accountant

  if (
    label1 === "auction agent" ||
    (label1 === "auction" && label2.includes("agent")) ||
    label1 === "buyer" ||
    label2.includes("buyer") ||
    label2.includes("logistics agent") ||
    combined === "logistics group"
  ) {
    return TopologyNodeIconKind.Supervisor
  }

  return TopologyNodeIconKind.Default
}

export function topologyNodeIconKind(
  input: TopologyNodeIconInput,
): TopologyNodeIconKind {
  const slug = normalize(input.directoryAgentSlug)
  if (slug) {
    const bySlug = iconKindFromSlug(slug)
    if (bySlug) return bySlug
  }
  return iconKindFromLabels(normalize(input.label1), normalize(input.label2))
}

function brandedImg(src: string, alt: string): React.ReactNode {
  return <GraphDiscoveryAssetImg src={src} alt={alt} invertInDarkMode />
}

export function resolveTopologyNodeIcon(
  input: TopologyNodeIconInput,
): React.ReactNode {
  switch (topologyNodeIconKind(input)) {
    case TopologyNodeIconKind.Supervisor:
      return brandedImg(supervisorIcon, "Supervisor Icon")
    case TopologyNodeIconKind.Recruiter:
      return brandedImg(supervisorIcon, "Recruiter Icon")
    case TopologyNodeIconKind.Directory:
      return brandedImg(supervisorIcon, "Directory Icon")
    case TopologyNodeIconKind.Farm:
      return brandedImg(farmAgentIcon, "Farm Agent Icon")
    case TopologyNodeIconKind.WeatherMcp:
      return <Air aria-hidden />
    case TopologyNodeIconKind.PaymentMcp:
      return <Calculate aria-hidden />
    case TopologyNodeIconKind.Shipping:
      return <LocalShipping aria-hidden />
    case TopologyNodeIconKind.Accountant:
      return <Calculate aria-hidden />
    default:
      return <SmartToy aria-hidden />
  }
}
