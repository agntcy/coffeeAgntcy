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
import {
  buildIdentityBadgeRequest,
  buildIdentityPolicyRequest,
  LUNGO_FRONTEND_URLS,
} from "@/urls"
import type { HttpRequestTarget } from "@/urls"
import { resolveAgentSlug } from "@/utils/resolveAgentSlug"
import { logger } from "@/utils/logger"

const IDENTITY_REQUEST_TIMEOUT_MS = 10_000

const getSlugFromNodeData = (nodeData: CustomNodeData): string => {
  logger.debug("getSlugFromNodeData", nodeData)
  return resolveAgentSlug(nodeData, "identity")
}

/** Same target as {@link fetchBadgeDetails} — for `reportRequestError` in modal catch. */
export function badgeDetailsRequest(
  nodeData: CustomNodeData,
): HttpRequestTarget {
  return buildIdentityBadgeRequest(getSlugFromNodeData(nodeData))
}

/** Same target as {@link fetchPolicyDetails} — for `reportRequestError` in modal catch. */
export function policyDetailsRequest(
  nodeData: CustomNodeData,
): HttpRequestTarget {
  return buildIdentityPolicyRequest(getSlugFromNodeData(nodeData))
}

/** For `reportRequestError` when slug resolution may have failed. */
export function badgeDetailsEndpointLabelForReport(
  nodeData: CustomNodeData,
): string {
  try {
    return badgeDetailsRequest(nodeData).endpointLabel
  } catch {
    return LUNGO_FRONTEND_URLS.apiPaths.identityAppsBadge("unknown")
      .endpointLabel
  }
}

/** For `reportRequestError` when slug resolution may have failed. */
export function policyDetailsEndpointLabelForReport(
  nodeData: CustomNodeData,
): string {
  try {
    return policyDetailsRequest(nodeData).endpointLabel
  } catch {
    return LUNGO_FRONTEND_URLS.apiPaths.identityAppsPolicies("unknown")
      .endpointLabel
  }
}

export const fetchBadgeDetails = async (
  nodeData: CustomNodeData,
): Promise<BadgeData> => {
  const request = badgeDetailsRequest(nodeData)
  return fetchJson<BadgeData>(request.url, {
    endpointLabel: request.endpointLabel,
    timeoutMs: IDENTITY_REQUEST_TIMEOUT_MS,
    headers: {
      "Content-Type": "application/json",
    },
  })
}

export const fetchPolicyDetails = async (
  nodeData: CustomNodeData,
): Promise<PolicyData> => {
  const request = policyDetailsRequest(nodeData)
  return fetchJson<PolicyData>(request.url, {
    endpointLabel: request.endpointLabel,
    timeoutMs: IDENTITY_REQUEST_TIMEOUT_MS,
    headers: {
      "Content-Type": "application/json",
    },
  })
}

export { getSlugFromNodeData }
