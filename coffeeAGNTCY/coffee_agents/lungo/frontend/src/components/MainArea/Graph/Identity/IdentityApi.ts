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
import { getApiUrlForPattern, PATTERNS } from "@/utils/patternUtils"
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

  if (nodeData.identityAppsSlug) {
    return nodeData.identityAppsSlug
  }

  if (nodeData.slug) {
    return nodeData.slug
  }

  const label = nodeData.label?.toLowerCase()
  const label_subtitle = nodeData.label_subtitle?.toLowerCase()

  if (
    label === "auction agent" ||
    label_subtitle?.includes("buyer") ||
    (label === "auction" && label_subtitle?.includes("agent"))
  ) {
    return "auction-supervisor"
  }

  if (label === "colombia" && label_subtitle?.includes("coffee farm")) {
    return "colombia-coffee-farm"
  }

  if (label === "vietnam" && label_subtitle?.includes("coffee farm")) {
    return "vietnam-coffee-farm"
  }

  if (label === "mcp server" && label_subtitle === "payment") {
    return "payment-mcp-server"
  }

  throw new Error(
    `No valid slug mapping found for node: ${label} ${label_subtitle}`,
  )
}

export const fetchBadgeDetails = async (
  nodeData: CustomNodeData,
): Promise<BadgeData> => {
  const slug = getSlugFromNodeData(nodeData)

  try {
    const response = await axios.get<BadgeData>(
      joinBaseUrl(
        getApiUrlForPattern(PATTERNS.PUBLISH_SUBSCRIBE),
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
        getApiUrlForPattern(PATTERNS.PUBLISH_SUBSCRIBE),
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
