/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  isVisibleSupplyChainMessage,
  parseSupplyChainEvent,
  supplyChainAddressees,
  supplyChainPartyLabel,
  type SupplyChainMessageEvent,
} from "./supplyChainEvents"

const message = {
  type: "message",
  seq: 1,
  from: "buyer",
  to: ["supplier_a"],
  kind: "negotiation",
  phase: "round_1",
  plan_version: 0,
  reply_to: null,
  body: "We need 1,000 tonnes.",
}

describe("parseSupplyChainEvent", () => {
  it("accepts a message and normalises optional fields", () => {
    const event = parseSupplyChainEvent({ ...message, phase: undefined })
    expect(event).toEqual({ ...message, phase: null })
  })

  it("rejects a message with a missing body", () => {
    expect(parseSupplyChainEvent({ ...message, body: undefined })).toBeNull()
  })

  it("accepts a status event", () => {
    expect(
      parseSupplyChainEvent({ type: "status", state: "round", round: 2 }),
    ).toEqual({ type: "status", state: "round", round: 2 })
  })

  it("defaults missing lists in a record", () => {
    const event = parseSupplyChainEvent({
      type: "record",
      record: { run_id: "r1", case: "ambiguous", status: "committed" },
    })
    expect(event?.type).toBe("record")
    if (event?.type === "record") {
      expect(event.record.lots).toEqual([])
      expect(event.record.confirmations).toEqual([])
    }
  })

  it("keeps the silent flag only when it is exactly true", () => {
    const base = { verdict: "FAIL", codes: ["LATE_LOT"] }
    const silent = parseSupplyChainEvent({
      type: "verdict",
      verdict: { ...base, silent: true },
    })
    const loud = parseSupplyChainEvent({
      type: "verdict",
      verdict: { ...base, silent: "yes" },
    })
    expect(silent?.type === "verdict" && silent.verdict.silent).toBe(true)
    expect(loud?.type === "verdict" && loud.verdict.silent).toBe(false)
  })

  it("rejects an unknown verdict value", () => {
    expect(
      parseSupplyChainEvent({ type: "verdict", verdict: { verdict: "MAYBE" } }),
    ).toBeNull()
  })

  it.each([null, "text", 3, [], { type: "unknown" }, {}])(
    "returns null for %j",
    (value) => {
      expect(parseSupplyChainEvent(value)).toBeNull()
    },
  )
})

describe("party labels", () => {
  it.each([
    ["buyer", "Buyer"],
    ["moderator", "Buyer"],
    ["supplier_b", "Supplier B"],
    ["logistics", "Logistics"],
    ["someone_else", "someone_else"],
  ])("labels %s as %s", (party, label) => {
    expect(supplyChainPartyLabel(party)).toBe(label)
  })

  it("summarises everyone as All parties", () => {
    expect(
      supplyChainAddressees([
        "buyer",
        "supplier_a",
        "supplier_b",
        "supplier_c",
        "logistics",
      ]),
    ).toBe("All parties")
  })

  it("lists a subset by label", () => {
    expect(supplyChainAddressees(["supplier_a", "logistics"])).toBe(
      "Supplier A, Logistics",
    )
  })
})

describe("isVisibleSupplyChainMessage", () => {
  const withKind = (kind: string) =>
    ({ ...message, kind }) as unknown as SupplyChainMessageEvent

  it.each([
    ["negotiation", true],
    ["event", true],
    ["confirm_request", true],
    ["confirm_reply", true],
    ["control", false],
    ["noop", false],
  ])("%s -> %s", (kind, expected) => {
    expect(isVisibleSupplyChainMessage(withKind(kind))).toBe(expected)
  })
})
