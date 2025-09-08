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

export const FarmName = {
  BrazilCoffeeFarm: "Brazil Coffee Farm",
  ColombiaCoffeeFarm: "Colombia Coffee Farm",
  VietnamCoffeeFarm: "Vietnam Coffee Farm",
} as const

export type RoleType = (typeof Role)[keyof typeof Role]
export type EdgeLabelIconType =
  (typeof EdgeLabelIcon)[keyof typeof EdgeLabelIcon]
export type FarmNameType = (typeof FarmName)[keyof typeof FarmName]
