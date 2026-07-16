/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import {
  BadgeData,
  PolicyData,
} from "@/components/MainArea/Graph/Identity/types"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import { fetchJson } from "@/api/http"
import { joinBaseUrl, LUNGO_FRONTEND_URLS } from "@/urls"
import { getApiUrlForChatTarget } from "@/utils/patternUtils"
import { resolveAgentSlug } from "@/utils/resolveAgentSlug"
import { logger } from "@/utils/logger"

const IDENTITY_REQUEST_TIMEOUT_MS = 10_000

const getSlugFromNodeData = (nodeData: CustomNodeData): string => {
  logger.debug("getSlugFromNodeData", nodeData)
  return resolveAgentSlug(nodeData, "identity")
}

export const fetchBadgeDetails = async (
  nodeData: CustomNodeData,
): Promise<BadgeData> => {
  const slug = getSlugFromNodeData(nodeData)
  const endpoint = LUNGO_FRONTEND_URLS.apiPaths.identityAppsBadge(slug)
  const url = joinBaseUrl(getApiUrlForChatTarget("exchange"), endpoint)

  return fetchJson<BadgeData>(url, {
    endpoint,
    timeoutMs: IDENTITY_REQUEST_TIMEOUT_MS,
    headers: {
      "Content-Type": "application/json",
    },
  })
}

export const fetchPolicyDetails = async (
  nodeData: CustomNodeData,
): Promise<PolicyData> => {
  const slug = getSlugFromNodeData(nodeData)
  const endpoint = LUNGO_FRONTEND_URLS.apiPaths.identityAppsPolicies(slug)
  const url = joinBaseUrl(getApiUrlForChatTarget("exchange"), endpoint)

  return fetchJson<PolicyData>(url, {
    endpoint,
    timeoutMs: IDENTITY_REQUEST_TIMEOUT_MS,
    headers: {
      "Content-Type": "application/json",
    },
  })
}

export { getSlugFromNodeData }
