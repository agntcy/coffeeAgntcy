/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Event shapes streamed by the Supply Chain Commitment buyer
 * (`POST /agent/prompt/stream`). Every NDJSON line is
 * `{"response": <event>, "session_id": "..."}` where `<event>` is a JSON
 * object discriminated by `type`.
 **/

export interface SupplyChainStatusEvent {
  type: "status"
  /** e.g. selected, started, round, decision, disruption, error, l9_disabled */
  state: string
  message?: string
  case?: string
  configuration?: string
  round?: number
  action?: string
  plan_version?: number
}

export interface SupplyChainMessageEvent {
  type: "message"
  seq: number
  from: string
  to: string[]
  kind: string
  phase: string | null
  plan_version: number | null
  reply_to: number | null
  body: string
}

export interface SupplyChainLotRecord {
  supplier: string
  tonnes: number
  grade?: string
  origin_ready_at?: string
  transport_option?: string
  claimed_arrival_at?: string
}

export interface SupplyChainConfirmation {
  party: string
  plan_version: number
  decision: string
  reason?: string
}

export interface SupplyChainRecord {
  run_id: string
  case: string
  configuration: string
  plan_version: number | null
  status: string
  reason?: string | null
  lots: SupplyChainLotRecord[]
  destination?: string
  arrival_deadline?: string
  total_cost_usd?: number | null
  confirmations: SupplyChainConfirmation[]
}

export interface SupplyChainLotCheck {
  supplier: string
  option?: string
  recomputed_arrival_at?: string | null
  on_time?: boolean
}

export interface SupplyChainVerdict {
  verdict: "PASS" | "FAIL" | "INVALID"
  codes: string[]
  details: string[]
  lots: SupplyChainLotCheck[]
  recomputed_total_cost_usd?: number | null
  /** True when the run failed and every party still confirmed the plan. */
  silent: boolean
}

export interface SupplyChainRecordEvent {
  type: "record"
  record: SupplyChainRecord
}

export interface SupplyChainVerdictEvent {
  type: "verdict"
  verdict: SupplyChainVerdict
}

export type SupplyChainStreamEvent =
  | SupplyChainStatusEvent
  | SupplyChainMessageEvent
  | SupplyChainRecordEvent
  | SupplyChainVerdictEvent

const isObject = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value)

/**
 * Narrow a parsed `response` value to a supply chain event. Returns null for
 * anything that is not one (including the logistics stream's own steps), so
 * callers can fall through to their other shapes.
 */
export function parseSupplyChainEvent(
  value: unknown,
): SupplyChainStreamEvent | null {
  if (!isObject(value) || typeof value.type !== "string") return null

  switch (value.type) {
    case "status":
      return typeof value.state === "string"
        ? (value as unknown as SupplyChainStatusEvent)
        : null
    case "message":
      if (
        typeof value.seq !== "number" ||
        typeof value.from !== "string" ||
        !Array.isArray(value.to) ||
        typeof value.kind !== "string" ||
        typeof value.body !== "string"
      ) {
        return null
      }
      return {
        type: "message",
        seq: value.seq,
        from: value.from,
        to: value.to.filter((t): t is string => typeof t === "string"),
        kind: value.kind,
        phase: typeof value.phase === "string" ? value.phase : null,
        plan_version:
          typeof value.plan_version === "number" ? value.plan_version : null,
        reply_to: typeof value.reply_to === "number" ? value.reply_to : null,
        body: value.body,
      }
    case "record":
      if (!isObject(value.record)) return null
      return {
        type: "record",
        record: {
          ...(value.record as unknown as SupplyChainRecord),
          lots: Array.isArray(value.record.lots)
            ? (value.record.lots as SupplyChainLotRecord[])
            : [],
          confirmations: Array.isArray(value.record.confirmations)
            ? (value.record.confirmations as SupplyChainConfirmation[])
            : [],
        },
      }
    case "verdict":
      if (!isObject(value.verdict)) return null
      if (
        value.verdict.verdict !== "PASS" &&
        value.verdict.verdict !== "FAIL" &&
        value.verdict.verdict !== "INVALID"
      ) {
        return null
      }
      return {
        type: "verdict",
        verdict: {
          ...(value.verdict as unknown as SupplyChainVerdict),
          codes: Array.isArray(value.verdict.codes)
            ? (value.verdict.codes as string[])
            : [],
          details: Array.isArray(value.verdict.details)
            ? (value.verdict.details as string[])
            : [],
          lots: Array.isArray(value.verdict.lots)
            ? (value.verdict.lots as SupplyChainLotCheck[])
            : [],
          silent: value.verdict.silent === true,
        },
      }
    default:
      return null
  }
}

/** Display label of a party id; matches the catalog node labels. */
export const SUPPLY_CHAIN_PARTY_LABELS: Readonly<Record<string, string>> = {
  buyer: "Buyer",
  moderator: "Buyer",
  supplier_a: "Supplier A",
  supplier_b: "Supplier B",
  supplier_c: "Supplier C",
  logistics: "Logistics",
}

export function supplyChainPartyLabel(party: string): string {
  return SUPPLY_CHAIN_PARTY_LABELS[party] ?? party
}

/** True for the five parties; false for the moderator-only sender. */
const ALL_PARTIES = [
  "buyer",
  "supplier_a",
  "supplier_b",
  "supplier_c",
  "logistics",
]

/** "All parties" when a message goes to everyone, else the labelled addressees. */
export function supplyChainAddressees(to: readonly string[]): string {
  const set = new Set(to)
  if (ALL_PARTIES.every((p) => set.has(p))) return "All parties"
  return to.map(supplyChainPartyLabel).join(", ")
}

/** Message kinds the feed shows as chat lines (control and noop are hidden). */
export function isVisibleSupplyChainMessage(
  event: SupplyChainMessageEvent,
): boolean {
  return event.kind !== "control" && event.kind !== "noop"
}
