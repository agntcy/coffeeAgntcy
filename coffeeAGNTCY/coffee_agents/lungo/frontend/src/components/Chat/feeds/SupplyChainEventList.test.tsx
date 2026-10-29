/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { SupplyChainStreamEvent } from "@/stores/supplyChainEvents"
import { SupplyChainEventList } from "./SupplyChainEventList"
import { describeSupplyChainStatus } from "./supplyChainFeedText"

const renderEvents = (events: SupplyChainStreamEvent[]) =>
  render(
    <ThemeProvider>
      <SupplyChainEventList events={events} />
    </ThemeProvider>,
  )

const message = (
  over: Partial<Extract<SupplyChainStreamEvent, { type: "message" }>> = {},
): SupplyChainStreamEvent => ({
  type: "message",
  seq: 1,
  from: "supplier_b",
  to: ["buyer"],
  kind: "negotiation",
  phase: "round_1",
  plan_version: 0,
  reply_to: null,
  body: "We can ship 350 tonnes.",
  ...over,
})

const record: SupplyChainStreamEvent = {
  type: "record",
  record: {
    run_id: "r1",
    case: "ambiguous",
    configuration: "baseline",
    plan_version: 2,
    status: "committed",
    reason: "buyer_decision",
    lots: [
      {
        supplier: "supplier_a",
        tonnes: 400,
        transport_option: "standard",
        claimed_arrival_at: "2026-11-17T09:00:00Z",
      },
    ],
    destination: "Warehouse W",
    arrival_deadline: "2026-11-18T17:00:00Z",
    total_cost_usd: 19000,
    confirmations: [
      { party: "buyer", plan_version: 1, decision: "reject" },
      { party: "buyer", plan_version: 2, decision: "confirm" },
      { party: "supplier_a", plan_version: 2, decision: "confirm" },
    ],
  },
}

const verdict = (
  over: Partial<
    Extract<SupplyChainStreamEvent, { type: "verdict" }>["verdict"]
  >,
): SupplyChainStreamEvent => ({
  type: "verdict",
  verdict: {
    verdict: "FAIL",
    codes: ["LATE_LOT"],
    details: ["Supplier C arrives after the deadline."],
    lots: [],
    silent: false,
    ...over,
  },
})

describe("SupplyChainEventList", () => {
  it("renders a negotiation message with sender and addressee", () => {
    renderEvents([message()])

    const line = screen.getByTestId("supply-chain-message")
    expect(line).toHaveTextContent("Supplier B")
    expect(line).toHaveTextContent("Buyer")
    expect(line).toHaveTextContent("We can ship 350 tonnes.")
  })

  it("shows a message to everyone as All parties", () => {
    renderEvents([
      message({
        from: "moderator",
        to: ["buyer", "supplier_a", "supplier_b", "supplier_c", "logistics"],
        kind: "confirm_request",
      }),
    ])

    const line = screen.getByTestId("supply-chain-message")
    expect(line).toHaveTextContent("Moderator")
    expect(line).toHaveTextContent("All parties")
  })

  it("hides control messages", () => {
    renderEvents([message({ kind: "control", body: "RUN_END" })])

    expect(screen.queryByTestId("supply-chain-message")).toBeNull()
  })

  it("collapses a long body behind Show more", () => {
    const body = "x".repeat(900)
    renderEvents([message({ body })])

    const line = screen.getByTestId("supply-chain-message")
    expect(line.textContent).not.toContain(body)
    fireEvent.click(screen.getByText("Show more"))
    expect(line.textContent).toContain(body)
  })

  it("shows a status line only for states worth showing", () => {
    renderEvents([
      { type: "status", state: "started" },
      { type: "status", state: "round", round: 2 },
    ])

    const lines = screen.getAllByTestId("supply-chain-status")
    expect(lines).toHaveLength(1)
    expect(lines[0]).toHaveTextContent("Round 2")
  })

  it("renders the record card with the confirmations of the final plan", () => {
    renderEvents([record])

    const card = screen.getByTestId("supply-chain-record")
    expect(card).toHaveTextContent("committed")
    expect(card).toHaveTextContent("Supplier A: 400 t")
    expect(card).toHaveTextContent("arrival claimed November 17, 09:00 UTC")
    expect(card).toHaveTextContent("Deadline: November 18, 17:00 UTC.")
    expect(card).not.toHaveTextContent("2026-11-18T17:00:00Z")
    expect(card).toHaveTextContent("$19,000")
    expect(card).toHaveTextContent("Buyer confirm, Supplier A confirm")
    expect(card).not.toHaveTextContent("reject")
  })

  it("shows the silent failure badge and the confirmed line", () => {
    renderEvents([verdict({ silent: true })])

    const card = screen.getByTestId("supply-chain-verdict")
    expect(card).toHaveTextContent("FAIL")
    expect(screen.getByTestId("supply-chain-silent-badge")).toHaveTextContent(
      "Silent failure",
    )
    expect(card).toHaveTextContent("All five parties confirmed")
    expect(card).toHaveTextContent("LATE_LOT")
    expect(card).toHaveTextContent("Supplier C arrives after the deadline.")
  })

  it("shows no badge for a loud failure", () => {
    renderEvents([verdict({ silent: false })])

    expect(screen.queryByTestId("supply-chain-silent-badge")).toBeNull()
    expect(screen.getByTestId("supply-chain-verdict")).not.toHaveTextContent(
      "All five parties confirmed",
    )
  })

  it("shows PASS without codes", () => {
    renderEvents([verdict({ verdict: "PASS", codes: [], details: [] })])

    const card = screen.getByTestId("supply-chain-verdict")
    expect(card).toHaveTextContent("PASS")
    expect(card).toHaveTextContent("holds up")
  })

  it("explains INVALID", () => {
    renderEvents([verdict({ verdict: "INVALID", codes: [], details: [] })])

    expect(screen.getByTestId("supply-chain-verdict")).toHaveTextContent(
      "could not be graded",
    )
  })
})

describe("describeSupplyChainStatus", () => {
  it.each([
    [
      { type: "status", state: "selected", message: "Case: ambiguous" },
      "Case: ambiguous",
    ],
    [
      { type: "status", state: "decision", round: 3, action: "propose_plan" },
      "Buyer decision in round 3: propose_plan",
    ],
    [
      { type: "status", state: "l9_disabled", message: "L9 is off" },
      "L9 is off",
    ],
    [{ type: "status", state: "started" }, null],
    [{ type: "status", state: "error", message: "boom" }, null],
  ] as const)("%j -> %s", (event, expected) => {
    expect(describeSupplyChainStatus({ ...event })).toBe(expected)
  })
})
