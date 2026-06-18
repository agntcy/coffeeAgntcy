/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it, vi } from "vitest"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"
import {
  fetchWorkflowSummaries,
  patternTypeFromSummary,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"

const makeSummary = (over: Partial<WorkflowSummary>): WorkflowSummary => ({
  name: "Workflow",
  pattern: "publish_subscribe",
  use_case: "use",
  scenario: "scenario",
  supports_sse: false,
  supports_streaming: false,
  chat_api_target: "exchange",
  ...over,
})

describe("patternTypeFromSummary", () => {
  it.each<{
    caseName: string
    over: Partial<WorkflowSummary>
    expected: PatternType | null
  }>([
    {
      caseName: "null chat_api_target yields no pattern",
      over: { chat_api_target: null },
      expected: null,
    },
    {
      caseName: "supports_sse maps to group messaging",
      over: { chat_api_target: "logistics", supports_sse: true },
      expected: PATTERNS.GROUP_MESSAGING,
    },
    {
      caseName: "supports_sse takes precedence over streaming flag",
      over: {
        chat_api_target: "logistics",
        supports_sse: true,
        supports_streaming: true,
      },
      expected: PATTERNS.GROUP_MESSAGING,
    },
    {
      caseName: "discovery maps to a2a http",
      over: { chat_api_target: "discovery" },
      expected: PATTERNS.A2A_HTTP,
    },
    {
      caseName: "discovery takes precedence over streaming flag",
      over: { chat_api_target: "discovery", supports_streaming: true },
      expected: PATTERNS.A2A_HTTP,
    },
    {
      caseName: "streaming exchange maps to publish subscribe streaming",
      over: { chat_api_target: "exchange", supports_streaming: true },
      expected: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
    },
    {
      caseName: "non-streaming exchange maps to publish subscribe",
      over: { chat_api_target: "exchange" },
      expected: PATTERNS.PUBLISH_SUBSCRIBE,
    },
    {
      caseName: "logistics target without supports_sse yields no pattern",
      over: { chat_api_target: "logistics", supports_sse: false },
      expected: null,
    },
  ])("$caseName", ({ over, expected }) => {
    expect(patternTypeFromSummary(makeSummary(over))).toBe(expected)
  })
})

describe("fetchWorkflowSummaries", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const stubFetch = (
    body: unknown,
    init: { ok?: boolean; status?: number; statusText?: string } = {},
  ): void => {
    const { ok = true, status = 200, statusText = "OK" } = init
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok,
        status,
        statusText,
        json: async () => body,
      })),
    )
  }

  it("parses rows, applies legacy defaults, and preserves key order", async () => {
    stubFetch({
      Streaming: {
        name: "Streaming",
        pattern: "publish_subscribe_streaming",
        use_case: "use",
        scenario: "scenario",
        supports_sse: false,
        supports_streaming: true,
        chat_api_target: "exchange",
      },
      Legacy: {
        name: "Legacy",
        pattern: "publish_subscribe",
        use_case: "use",
        scenario: "scenario",
      },
    })

    const summaries = await fetchWorkflowSummaries()

    expect(summaries.map((s) => s.name)).toEqual(["Streaming", "Legacy"])
    expect(summaries[0]).toMatchObject({
      supports_streaming: true,
      chat_api_target: "exchange",
    })
    expect(summaries[1]).toMatchObject({
      supports_sse: false,
      supports_streaming: false,
      chat_api_target: null,
    })
  })

  it("skips rows missing required string fields", async () => {
    stubFetch({
      Good: {
        name: "Good",
        pattern: "publish_subscribe",
        use_case: "use",
        scenario: "scenario",
      },
      Bad: { pattern: "publish_subscribe" },
    })

    const summaries = await fetchWorkflowSummaries()

    expect(summaries.map((s) => s.name)).toEqual(["Good"])
  })

  it("drops invalid chat_api_target to null", async () => {
    stubFetch({
      Weird: {
        name: "Weird",
        pattern: "publish_subscribe",
        use_case: "use",
        scenario: "scenario",
        chat_api_target: "nonsense",
      },
    })

    const summaries = await fetchWorkflowSummaries()

    expect(summaries[0].chat_api_target).toBeNull()
  })

  it.each([
    {
      caseName: "non-ok response throws",
      body: {},
      init: { ok: false, status: 500, statusText: "Server Error" },
    },
    {
      caseName: "array response shape throws",
      body: [],
      init: {},
    },
  ])("$caseName", async ({ body, init }) => {
    stubFetch(body, init)
    await expect(fetchWorkflowSummaries()).rejects.toThrow()
  })
})
