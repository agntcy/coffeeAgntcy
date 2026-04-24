/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { PATTERNS } from "@/utils/patternUtils"
import type { Story } from "../types"

export const coffeeInventoryStory: Story = {
  id: "coffee-inventory",
  title: "Coffee Inventory Tour",
  description: "Check inventory across origin countries.",
  pattern: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
  defaultPauseAfterMs: 2500,
  defaultMaxWaitMs: 60_000,
  steps: [
    {
      kind: "narration",
      text: "Let's take a quick tour of global coffee inventory.",
      durationMs: 2500,
    },
    { kind: "prompt", prompt: "what inventory does Brazil have?" },
    { kind: "prompt", prompt: "what inventory does Colombia have?" },
    {
      kind: "narration",
      text: "Tour complete — you've seen both origins' stock.",
      durationMs: 3000,
    },
  ],
}
