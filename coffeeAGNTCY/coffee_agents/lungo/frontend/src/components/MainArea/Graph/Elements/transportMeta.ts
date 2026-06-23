/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { OasfRecord } from "../Directory/DirectoryApi"

export type KnownTransportName = "slimrpc" | "slim" | "nats" | "jsonrpc"

export interface AgentTransport {
  name: string
  url?: string
  preferred?: boolean
}

export interface TransportMeta {
  short: string
  label: string
}

export const TRANSPORT_META: Record<
  KnownTransportName | "unknown",
  TransportMeta
> = {
  slimrpc: {
    short: "SLIM RPC",
    label: "Point-to-point RPC",
  },
  slim: {
    short: "SLIM",
    label: "Group messaging / broadcast",
  },
  nats: {
    short: "NATS",
    label: "Pub-sub / broadcast",
  },
  jsonrpc: {
    short: "HTTP",
    label: "JSON-RPC",
  },
  unknown: {
    short: "OTHER",
    label: "Additional agent interface",
  },
}

interface AgentInterfaceWire {
  transport?: unknown
  url?: unknown
}

interface A2aCardDataWire {
  additionalInterfaces?: unknown
  additional_interfaces?: unknown
  preferredTransport?: unknown
  preferred_transport?: unknown
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function normalizeTransportName(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : ""
}

export function transportMetaFor(name: string | undefined): TransportMeta {
  const normalized = normalizeTransportName(name)
  if (
    normalized === "slimrpc" ||
    normalized === "slim" ||
    normalized === "nats" ||
    normalized === "jsonrpc"
  ) {
    return TRANSPORT_META[normalized]
  }
  return {
    ...TRANSPORT_META.unknown,
    short: normalized ? normalized.toUpperCase() : TRANSPORT_META.unknown.short,
  }
}

function readCardData(record: OasfRecord): A2aCardDataWire | null {
  const modules = Array.isArray(record.modules) ? record.modules : []
  for (const module of modules) {
    if (!isRecord(module)) continue
    const data = module.data
    if (!isRecord(data)) continue
    const cardData = data.card_data
    if (isRecord(cardData)) return cardData as A2aCardDataWire
  }
  return null
}

function readInterfaces(cardData: A2aCardDataWire): AgentInterfaceWire[] {
  const interfaces =
    cardData.additionalInterfaces ?? cardData.additional_interfaces
  if (!Array.isArray(interfaces)) return []
  return interfaces.filter(isRecord) as AgentInterfaceWire[]
}

export function extractA2aTransportsFromOasf(
  record: OasfRecord,
): AgentTransport[] {
  const cardData = readCardData(record)
  if (!cardData) return []

  const preferred = normalizeTransportName(
    cardData.preferredTransport ?? cardData.preferred_transport,
  )
  const seen = new Set<string>()

  const transports: AgentTransport[] = []

  for (const entry of readInterfaces(cardData)) {
    const name = normalizeTransportName(entry.transport)
    if (!name || seen.has(name)) continue
    seen.add(name)
    transports.push({
      name,
      url: typeof entry.url === "string" ? entry.url : undefined,
      preferred: preferred ? name === preferred : false,
    })
  }

  return transports
}
