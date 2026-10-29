/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Plain-text helpers for the Supply Chain Commitment feed.
 **/

import {
  supplyChainPartyLabel,
  type SupplyChainStatusEvent,
} from "@/stores/supplyChainEvents"

/** Sender shown in the feed. The moderator speaks as itself, not as the Buyer. */
export function supplyChainSenderName(party: string): string {
  return party === "moderator" ? "Moderator" : supplyChainPartyLabel(party)
}

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
]

/**
 * An ISO timestamp as people read it, e.g. "November 18, 17:00 UTC", the same
 * wording the agents use in their briefs. Returns the input unchanged when it
 * is not a valid date.
 */
export function formatSupplyChainTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const hh = String(date.getUTCHours()).padStart(2, "0")
  const mm = String(date.getUTCMinutes()).padStart(2, "0")
  return `${MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}, ${hh}:${mm} UTC`
}

/** One line for a status event, or null when the event is not worth showing. */
export function describeSupplyChainStatus(
  event: SupplyChainStatusEvent,
): string | null {
  switch (event.state) {
    case "selected":
      return (
        event.message ??
        `Case ${event.case ?? "?"}, run type ${event.configuration ?? "?"}`
      )
    case "round":
      return `Round ${event.round ?? "?"}`
    case "decision":
      return `Buyer decision in round ${event.round ?? "?"}: ${event.action ?? "?"}`
    case "disruption":
      return `Disruption after plan version ${event.plan_version ?? "?"} was confirmed: a supplier's ready time changed`
    case "l9_disabled":
    case "not_implemented":
      return event.message ?? event.state
    default:
      return null
  }
}
