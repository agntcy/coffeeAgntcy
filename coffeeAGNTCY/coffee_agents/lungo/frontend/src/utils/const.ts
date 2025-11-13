/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

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
} as const

export const FarmName = {
  BrazilCoffeeFarm: "Brazil Coffee Farm",
  ColombiaCoffeeFarm: "Colombia Coffee Farm",
  VietnamCoffeeFarm: "Vietnam Coffee Farm",
} as const

export const NODE_IDS = {
  AUCTION_AGENT: "1",
  TRANSPORT: "2",
  BRAZIL_FARM: "3",
  COLOMBIA_FARM: "4",
  VIETNAM_FARM: "5",
  WEATHER_MCP: "6",
  PAYMENT_MCP: "7",
  LOGISTICS_GROUP: "logistics-group",
} as const

export const EDGE_IDS = {
  AUCTION_TO_TRANSPORT: "1-2",
  TRANSPORT_TO_BRAZIL: "2-3",
  TRANSPORT_TO_COLOMBIA: "2-4",
  TRANSPORT_TO_VIETNAM: "2-5",
  COLOMBIA_TO_MCP: "4-mcp",
  SUPERVISOR_TO_TRANSPORT: "1-2",
  FARM_TO_TRANSPORT: "3-2",
  TRANSPORT_TO_SHIPPER: "2-4",
  TRANSPORT_TO_ACCOUNTANT: "2-5",
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
export type FarmNameType = (typeof FarmName)[keyof typeof FarmName]
export type NodeIdType = (typeof NODE_IDS)[keyof typeof NODE_IDS]
export type EdgeIdType = (typeof EDGE_IDS)[keyof typeof EDGE_IDS]
export type NodeTypeType = (typeof NODE_TYPES)[keyof typeof NODE_TYPES]
export type EdgeTypeType = (typeof EDGE_TYPES)[keyof typeof EDGE_TYPES]
export type EdgeLabelType = (typeof EDGE_LABELS)[keyof typeof EDGE_LABELS]
export type HandleTypeType = (typeof HANDLE_TYPES)[keyof typeof HANDLE_TYPES]
export type VerificationStatusType =
  (typeof VERIFICATION_STATUS)[keyof typeof VERIFICATION_STATUS]
