/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from "vitest"
import { GROUP_MESSAGING_CONFIG } from "@/utils/graphConfigsData"
import { NODE_IDS } from "@/utils/const"
import {
  animationSequenceStepIds,
  resolveStreamAuthorToNodeId,
} from "./chatStreamGraphHighlight"

describe("resolveStreamAuthorToNodeId", () => {
  it("maps recruiter service author to the recruiter node", () => {
    expect(resolveStreamAuthorToNodeId("recruiter_service")).toBe(
      NODE_IDS.RECRUITER,
    )
  })

  it("maps group stream supervisor to the buyer node", () => {
    expect(
      resolveStreamAuthorToNodeId("Supervisor", GROUP_MESSAGING_CONFIG),
    ).toBe(NODE_IDS.AUCTION_AGENT)
  })
})

describe("animationSequenceStepIds", () => {
  it("returns ids for a valid step index", () => {
    expect(animationSequenceStepIds(GROUP_MESSAGING_CONFIG, 0)).toEqual([
      NODE_IDS.AUCTION_AGENT,
    ])
  })

  it("returns empty when step is out of range", () => {
    expect(animationSequenceStepIds(GROUP_MESSAGING_CONFIG, 99)).toEqual([])
  })
})
