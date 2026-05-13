/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import axios from "axios"
import { getApiUrlForPattern, PATTERNS } from "@/utils/patternUtils"
import { IdentityServiceError } from "@/components/MainArea/Graph/Identity/IdentityApi"
import type { CustomNodeData } from "../Elements/types"
import { getOasfSlugFromNodeData } from "@/utils/agenticTopologyIdentityUiMap"

export { getOasfSlugFromNodeData }

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

/** OASF record from directory API; URL fields used for link in modal. */
export interface OasfRecord {
  /** Directory URL (snake_case from API). */
  directory_url?: string
  /** Directory URL (camelCase variant). */
  directoryUrl?: string
  url?: string
  [key: string]: unknown
}

/** Node data that may already include a cached OASF record. */
type NodeDataForOasf =
  | (CustomNodeData & { oasfRecord?: OasfRecord })
  | null
  | undefined

const OASF_FETCH_CACHE_MAX = 24
const oasfFetchCache = new Map<string, OasfRecord>()

function oasfCacheKey(pattern: string, slug: string): string {
  return `${pattern}\0${slug}`
}

export const fetchOasfRecord = async (
  nodeData: NodeDataForOasf,
): Promise<OasfRecord> => {
  if (nodeData?.oasfRecord) {
    return nodeData.oasfRecord
  }

  const slug = getOasfSlugFromNodeData(nodeData)

  let pattern: string = PATTERNS.PUBLISH_SUBSCRIBE
  if (
    slug === "logistics-supervisor-agent" ||
    slug === "tatooine-farm-agent" ||
    slug === "shipping-agent" ||
    slug === "accountant-agent"
  ) {
    pattern = PATTERNS.GROUP_COMMUNICATION
  }

  const cacheKey = oasfCacheKey(pattern, slug)
  const cached = oasfFetchCache.get(cacheKey)
  if (cached) {
    return cached
  }

  try {
    const response = await axios.get<OasfRecord>(
      `${getApiUrlForPattern(pattern)}/agents/${slug}/oasf`,
      {
        timeout: 10000,
        headers: {
          "Content-Type": "application/json",
        },
      },
    )

    if (oasfFetchCache.size >= OASF_FETCH_CACHE_MAX) {
      const first = oasfFetchCache.keys().next().value
      if (first !== undefined) oasfFetchCache.delete(first)
    }
    oasfFetchCache.set(cacheKey, response.data)

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage =
        messageFromAxiosResponse(error) ||
        error.message ||
        "Failed to fetch OASF record"

      const errorStatus = error.response?.status

      throw {
        message: errorMessage,
        status: errorStatus,
      } as IdentityServiceError
    }

    throw {
      message: "An unexpected error occurred while fetching OASF record",
    } as IdentityServiceError
  }
}
