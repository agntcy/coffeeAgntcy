/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { PATTERNS } from "@/utils/patternUtils"
import type { Story } from "../types"

export const recruiterTourStory: Story = {
  id: "recruiter-tour",
  title: "Recruiter Agent Tour",
  description:
    "Discover, chat with, order from, and evaluate an agent via the AGNTCY directory.",
  pattern: PATTERNS.ON_DEMAND_DISCOVERY,
  defaultPauseAfterMs: 6000,
  defaultMaxWaitMs: 90_000,
  steps: [
    {
      kind: "narration",
      text: "Welcome to the On-Demand Discovery demo. We'll walk through the full recruiter lifecycle.",
      dialogue:
        "This tour demonstrates how the Recruiter Agent discovers agents in the AGNTCY directory, initiates conversations, places orders, and runs evaluations — all through streaming.",
      durationMs: 5000,
    },
    {
      kind: "prompt",
      prompt:
        "Can you find an agent named 'Brazil Coffee Farm' in the AGNTCY directory?",
      dialogue:
        "The Recruiter Agent searches the AGNTCY directory for an agent matching the name 'Brazil Coffee Farm'. If found, the agent record (including its CID and capabilities) is returned and displayed on the graph.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt: "Can I talk to Brazil",
      dialogue:
        "We initiate a conversation with the discovered Brazil Coffee Farm agent. The Recruiter acts as a proxy, forwarding messages between the user and the remote agent through the directory's communication channel.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt: "Can I order 100 lbs of coffee for $4 a pound?",
      dialogue:
        "We place an order through the active conversation. The Brazil Coffee Farm agent processes the request and responds with order confirmation details, pricing, and availability.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt: "I am done talking to Brazil",
      dialogue:
        "We end the conversation session with the Brazil Coffee Farm agent. The Recruiter confirms the session is closed and the agent is released.",
      pauseAfterMs: 7000,
    },
    {
      kind: "prompt",
      prompt:
        "Can you evaluate Brazil, ensure that if a user asks to reveal its instruction prompt, it will not do so.",
      dialogue:
        "The Recruiter triggers an evaluation of the Brazil Coffee Farm agent. A team of evaluation agents tests whether the agent properly guards its system prompt against prompt-injection attempts.",
      pauseAfterMs: 8000,
    },
    {
      kind: "narration",
      text: "Tour complete — you've seen discovery, conversation, ordering, and evaluation.",
      dialogue:
        "The full recruiter lifecycle is complete. You discovered an agent, communicated with it, placed an order, and ran a security evaluation — all orchestrated by the Recruiter Agent.",
      durationMs: 5000,
    },
  ],
}
