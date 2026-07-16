/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { PATTERNS } from "@/utils/patternUtils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import {
  deriveWorkflowCapabilities,
  isChatEnabledWorkflow,
  patternTypeFromSummary,
  workflowChatTransport,
  workflowChatUiMode,
} from "@/utils/workflowCapabilities"

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

describe("workflowCapabilities", () => {
  describe("deriveWorkflowCapabilities / patternTypeFromSummary", () => {
    it.each([
      {
        caseName: "null chat_api_target yields no capabilities",
        over: { chat_api_target: null },
        pattern: null,
        transport: null,
      },
      {
        caseName: "supports_sse maps to group messaging",
        over: { chat_api_target: "logistics" as const, supports_sse: true },
        pattern: PATTERNS.GROUP_MESSAGING,
        transport: "group_sse" as const,
      },
      {
        caseName: "discovery maps to a2a http",
        over: { chat_api_target: "discovery" as const },
        pattern: PATTERNS.A2A_HTTP,
        transport: "recruiter_stream" as const,
      },
      {
        caseName: "streaming exchange maps to publish subscribe streaming",
        over: {
          chat_api_target: "exchange" as const,
          supports_streaming: true,
        },
        pattern: PATTERNS.PUBLISH_SUBSCRIBE_STREAMING,
        transport: "auction_stream" as const,
      },
      {
        caseName: "non-streaming exchange maps to publish subscribe",
        over: { chat_api_target: "exchange" as const },
        pattern: PATTERNS.PUBLISH_SUBSCRIBE,
        transport: "plain_post" as const,
      },
    ])("$caseName", ({ over, pattern, transport }) => {
      const summary = makeSummary(over)
      expect(patternTypeFromSummary(summary)).toBe(pattern)
      expect(workflowChatTransport(summary)).toBe(transport)
      if (transport === null) {
        expect(deriveWorkflowCapabilities(summary)).toBeNull()
      } else {
        expect(deriveWorkflowCapabilities(summary)).toEqual({
          transport,
          pattern,
        })
      }
    })
  })

  describe("isChatEnabledWorkflow", () => {
    it.each([
      {
        caseName: "chat disabled when chat_api_target is null",
        over: { chat_api_target: null },
        expected: false,
      },
      {
        caseName: "chat enabled for exchange plain post",
        over: { chat_api_target: "exchange" as const },
        expected: true,
      },
      {
        caseName: "chat disabled for logistics without sse",
        over: { chat_api_target: "logistics" as const, supports_sse: false },
        expected: false,
      },
    ])("$caseName", ({ over, expected }) => {
      expect(isChatEnabledWorkflow(makeSummary(over))).toBe(expected)
    })
  })

  describe("workflowChatUiMode", () => {
    it.each([
      {
        caseName: "group sse UI mode",
        over: { chat_api_target: "logistics" as const, supports_sse: true },
        expected: {
          showProgressTracker: true,
          usesAuctionStreamPanel: false,
          usesRecruiterStreamPanel: false,
          usesPlainFinalResponse: false,
          isGroupMessaging: true,
        },
      },
      {
        caseName: "auction stream UI mode",
        over: {
          chat_api_target: "exchange" as const,
          supports_streaming: true,
        },
        expected: {
          showProgressTracker: false,
          usesAuctionStreamPanel: true,
          usesRecruiterStreamPanel: false,
          usesPlainFinalResponse: false,
          isGroupMessaging: false,
        },
      },
      {
        caseName: "plain post UI mode",
        over: { chat_api_target: "exchange" as const },
        expected: {
          showProgressTracker: false,
          usesAuctionStreamPanel: false,
          usesRecruiterStreamPanel: false,
          usesPlainFinalResponse: true,
          isGroupMessaging: false,
        },
      },
    ])("$caseName", ({ over, expected }) => {
      expect(workflowChatUiMode(makeSummary(over))).toEqual(expected)
    })
  })
})
