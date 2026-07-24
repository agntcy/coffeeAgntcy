/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Public workflow routing API: catalog capability derivation and chat backend URLs.
 * App code should import from this module only — not workflowCapabilities or
 * workflowChatRouting directly.
 */

export {
  deriveWorkflowCapabilities,
  isChatEnabledWorkflow,
  patternTypeFromSummary,
  workflowChatTransport,
  workflowChatUiMode,
  type WorkflowCapabilities,
  type WorkflowChatTransport,
  type WorkflowChatUiMode,
} from "@/utils/workflowCapabilities"

export {
  getAgentPromptRequestForWorkflow,
  getAgentPromptStreamRequestForWorkflow,
  getAgentPromptStreamUrlForWorkflow,
  getAgentPromptUrlForWorkflow,
  getApiBaseUrlForWorkflow,
  getSuggestedPromptsRequestForWorkflow,
  getSuggestedPromptsUrlForWorkflow,
  shouldEnableRetriesForWorkflow,
} from "@/utils/workflowChatRouting"
