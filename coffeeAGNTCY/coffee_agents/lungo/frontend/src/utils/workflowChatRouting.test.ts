/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  getDiscoveryAppApiUrl,
  getExchangeAppApiUrl,
  getLogisticsAppApiUrl,
  LUNGO_FRONTEND_URLS,
} from "@/urls"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  getAgentPromptStreamUrlForWorkflow,
  getAgentPromptUrlForWorkflow,
  getApiBaseUrlForWorkflow,
  getSuggestedPromptsUrlForWorkflow,
  shouldEnableRetriesForWorkflow,
  workflowChatTransport,
} from "@/utils/workflow"

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

describe("workflowChatRouting", () => {
  describe("getApiBaseUrlForWorkflow", () => {
    it.each([
      {
        caseName: "logistics target",
        over: { chat_api_target: "logistics" as const },
        expected: getLogisticsAppApiUrl(),
      },
      {
        caseName: "discovery target",
        over: { chat_api_target: "discovery" as const },
        expected: getDiscoveryAppApiUrl(),
      },
      {
        caseName: "exchange target",
        over: { chat_api_target: "exchange" as const },
        expected: getExchangeAppApiUrl(),
      },
      {
        caseName: "null summary defaults to exchange",
        over: {},
        summary: null,
        expected: getExchangeAppApiUrl(),
      },
    ])("$caseName", ({ over, summary, expected }) => {
      expect(getApiBaseUrlForWorkflow(summary ?? makeSummary(over))).toBe(
        expected,
      )
    })
  })

  describe("workflowChatTransport", () => {
    it.each([
      {
        caseName: "null chat_api_target",
        over: { chat_api_target: null },
        expected: null,
      },
      {
        caseName: "group sse",
        over: { chat_api_target: "logistics" as const, supports_sse: true },
        expected: "group_sse" as const,
      },
      {
        caseName: "discovery recruiter stream",
        over: { chat_api_target: "discovery" as const },
        expected: "recruiter_stream" as const,
      },
      {
        caseName: "discovery wins over streaming flag",
        over: {
          chat_api_target: "discovery" as const,
          supports_streaming: true,
        },
        expected: "recruiter_stream" as const,
      },
      {
        caseName: "auction stream",
        over: {
          chat_api_target: "exchange" as const,
          supports_streaming: true,
        },
        expected: "auction_stream" as const,
      },
      {
        caseName: "plain post",
        over: { chat_api_target: "exchange" as const },
        expected: "plain_post" as const,
      },
    ])("$caseName", ({ over, expected }) => {
      expect(workflowChatTransport(makeSummary(over))).toBe(expected)
    })
  })

  it("builds agent prompt URLs on workflow base", () => {
    const summary = makeSummary({ chat_api_target: "discovery" })
    expect(getAgentPromptUrlForWorkflow(summary)).toBe(
      `${getDiscoveryAppApiUrl()}${LUNGO_FRONTEND_URLS.apiPaths.agentPrompt}`,
    )
    expect(getAgentPromptStreamUrlForWorkflow(summary)).toBe(
      `${getDiscoveryAppApiUrl()}${LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream}`,
    )
  })

  it("uses streaming suggested prompts path when supports_streaming", () => {
    const summary = makeSummary({
      chat_api_target: "exchange",
      supports_streaming: true,
    })
    expect(getSuggestedPromptsUrlForWorkflow(summary)).toContain(
      LUNGO_FRONTEND_URLS.apiPaths.suggestedPromptsStreaming,
    )
  })

  it("shouldEnableRetriesForWorkflow follows supports_sse", () => {
    expect(
      shouldEnableRetriesForWorkflow(
        makeSummary({ supports_sse: true, chat_api_target: "logistics" }),
      ),
    ).toBe(true)
    expect(shouldEnableRetriesForWorkflow(makeSummary({}))).toBe(false)
  })

  it("getSuggestedPromptsUrlForWorkflow returns null when chat disabled", () => {
    expect(
      getSuggestedPromptsUrlForWorkflow(makeSummary({ chat_api_target: null })),
    ).toBeNull()
  })
})
