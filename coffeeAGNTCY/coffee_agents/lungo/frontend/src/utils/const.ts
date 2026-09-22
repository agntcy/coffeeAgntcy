/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { env } from "./env"

export const Role = {
  ASSISTANT: "assistant",
  USER: "user",
} as const

export const EdgeLabelIcon = {
  A2A: "a2a",
  MCP: "mcp",
} as const

export const EDGE_LABELS = {
  A2A: "A2A",
  MCP: "MCP: ",
  A2A_OVER_HTTP: "A2A: HTTP",
  MCP_WITH_STDIO: "MCP: stdio -> grpc",
} as const

export const NODE_TYPES = {
  CUSTOM: "customNode",
  TRANSPORT: "transportNode",
  GROUP: "group",
} as const

/** Event `type` values. Must match Python `schema.node_types`. */
export const NODE_TYPE = {
  AGENT: "agent",
  MCP: "mcp",
  DIRECTORY: "directory",
  GROUP: "group",
  TRANSPORT: "transport",
  CUSTOM_NODE: "customNode",
  TRANSPORT_NODE: "transportNode",
} as const

export type KnownNodeType = (typeof NODE_TYPE)[keyof typeof NODE_TYPE]

export function canonicalizeNodeType(
  raw: string | undefined,
): string | undefined {
  if (raw === NODE_TYPE.TRANSPORT_NODE) {
    return NODE_TYPE.TRANSPORT
  }
  return raw
}

export function isTransportType(type: string | undefined): boolean {
  return type === NODE_TYPE.TRANSPORT
}

export function isGroupType(type: string | undefined): boolean {
  return type === NODE_TYPE.GROUP
}

export function isAgentType(type: string | undefined): boolean {
  return type === NODE_TYPE.AGENT
}

export function isMcpType(type: string | undefined): boolean {
  return type === NODE_TYPE.MCP
}

export function isDirectoryType(type: string | undefined): boolean {
  return type === NODE_TYPE.DIRECTORY
}

export function nodeTypeToDisplayType(type: string | undefined): NodeTypeType {
  if (isTransportType(type)) {
    return NODE_TYPES.TRANSPORT
  }
  if (isGroupType(type)) {
    return NODE_TYPES.GROUP
  }
  return NODE_TYPES.CUSTOM
}

export const EDGE_TYPES = {
  CUSTOM: "custom",
  BRANCHING: "branching",
} as const

export const HANDLE_TYPES = {
  SOURCE: "source",
  TARGET: "target",
  ALL: "all",
} as const

export const VERIFICATION_STATUS = {
  VERIFIED: "verified",
  FAILED: "failed",
} as const

export type RoleType = (typeof Role)[keyof typeof Role]
export type EdgeLabelIconType =
  (typeof EdgeLabelIcon)[keyof typeof EdgeLabelIcon]
export type NodeTypeType = (typeof NODE_TYPES)[keyof typeof NODE_TYPES]
export type EdgeTypeType = (typeof EDGE_TYPES)[keyof typeof EDGE_TYPES]
export type EdgeLabelType = (typeof EDGE_LABELS)[keyof typeof EDGE_LABELS]
export type HandleTypeType = (typeof HANDLE_TYPES)[keyof typeof HANDLE_TYPES]
export type VerificationStatusType =
  (typeof VERIFICATION_STATUS)[keyof typeof VERIFICATION_STATUS]

export const isLocalDev =
  env.dev ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
