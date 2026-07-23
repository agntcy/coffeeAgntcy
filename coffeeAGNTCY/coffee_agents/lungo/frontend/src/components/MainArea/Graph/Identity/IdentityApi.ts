/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import axios from "axios"
import {
  BadgeData,
  PolicyData,
} from "@/components/MainArea/Graph/Identity/types"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import { joinBaseUrl, LUNGO_FRONTEND_URLS } from "@/urls"
import { getApiUrlForChatTarget } from "@/utils/patternUtils"
import { resolveAgentSlug } from "@/utils/resolveAgentSlug"
import { logger } from "@/utils/logger"

export interface IdentityServiceError {
  message: string
  status?: number
}

function messageFromAxiosResponse(error: unknown): string | undefined {
  if (!axios.isAxiosError(error) || error.response?.data == null)
    return undefined
  const d = error.response.data as { detail?: unknown; message?: unknown }
  if (typeof d.detail === "string") return d.detail
  if (Array.isArray(d.detail)) {
    return d.detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : String(item),
      )
      .join("; ")
  }
  if (typeof d.message === "string") return d.message
  return undefined
}

const getSlugFromNodeData = (nodeData: CustomNodeData): string => {
  logger.debug("getSlugFromNodeData", nodeData)
  return resolveAgentSlug(nodeData, "identity")
}

export const fetchBadgeDetails = async (
  nodeData: CustomNodeData,
): Promise<BadgeData> => {
  const slug = getSlugFromNodeData(nodeData)

  try {
    const response = await axios.get<BadgeData>(
      joinBaseUrl(
        getApiUrlForChatTarget("exchange"),
        LUNGO_FRONTEND_URLS.apiPaths.identityAppsBadge(slug),
      ),
      {
        timeout: 10000,
        headers: {
          "Content-Type": "application/json",
        },
      },
    )

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage =
        messageFromAxiosResponse(error) ||
        error.message ||
        "Failed to fetch badge details"
      const errorStatus = error.response?.status

      throw {
        message: errorMessage,
        status: errorStatus,
      } as IdentityServiceError
    }

    throw {
      message: "An unexpected error occurred while fetching badge details",
    } as IdentityServiceError
  }
}

export const fetchPolicyDetails = async (
  nodeData: CustomNodeData,
): Promise<PolicyData> => {
  const slug = getSlugFromNodeData(nodeData)

  try {
    const response = await axios.get<PolicyData>(
      joinBaseUrl(
        getApiUrlForChatTarget("exchange"),
        LUNGO_FRONTEND_URLS.apiPaths.identityAppsPolicies(slug),
      ),
      {
        timeout: 10000,
        headers: {
          "Content-Type": "application/json",
        },
      },
    )

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage =
        messageFromAxiosResponse(error) ||
        error.message ||
        "Failed to fetch policy details"
      const errorStatus = error.response?.status

      throw {
        message: errorMessage,
        status: errorStatus,
      } as IdentityServiceError
    }

    throw {
      message: "An unexpected error occurred while fetching policy details",
    } as IdentityServiceError
  }
}

export { getSlugFromNodeData }
