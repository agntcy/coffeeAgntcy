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
