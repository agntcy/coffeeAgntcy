/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { PATTERNS } from "@/utils/patternUtils"
import type { Story } from "../types"

export const coffeeInventoryStory: Story = {
  id: "coffee-inventory",
  title: "Coffee Inventory & Ordering Tour",
  description: "Check inventory across origin countries and place orders.",
  pattern: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
  defaultPauseAfterMs: 6000,
  defaultMaxWaitMs: 60_000,
  steps: [
    {
      kind: "narration",
      text: "Let's explore global coffee inventory and place some orders.",
      dialogue:
        "This tour queries individual farm agents for their stock, aggregates totals, and then places orders through the auction streaming transport.",
      durationMs: 4000,
    },
    {
      kind: "prompt",
      prompt: "what is the inventory for Vietnam?",
      dialogue:
        "We query the Vietnam Farm agent for its current inventory. The request flows through the publish-subscribe transport and returns available lots, grades, and quantities via streaming.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt: "what is the total inventory from all participating farms?",
      dialogue:
        "The Auction Agent fans out a request to every registered farm agent and aggregates their responses into a combined inventory summary.",
      pauseAfterMs: 7000,
    },
    {
      kind: "narration",
      text: "Now let's place a couple of orders.",
      dialogue:
        "With inventory confirmed, we'll submit purchase orders to individual farm agents through the same streaming transport.",
      durationMs: 3000,
    },
    {
      kind: "prompt",
      prompt:
        "I'd like to buy 200 lbs quantity of coffee at USD 500 price from Colombia",
      dialogue:
        "We place an order with the Colombia Farm agent for 200 lbs at $500. Colombia has a verified identity badge with an order flow policy, so the request passes Task-Based Access Control (TBAC) validation before executing the order.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt: "I'd like to buy 100 lbs of coffee at USD 250 price from Brazil",
      dialogue:
        "This order targets the Brazil Farm agent, which lacks a verified identity badge. The Task-Based Access Control (TBAC) system will reject the request, demonstrating how identity verification protects the supply chain.",
      pauseAfterMs: 8000,
    },
  ],
}
