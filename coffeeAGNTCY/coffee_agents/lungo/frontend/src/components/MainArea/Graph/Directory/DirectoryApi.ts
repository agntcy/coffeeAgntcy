/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import axios from "axios"
import { getApiUrlForPattern, PATTERNS } from "@/utils/patternUtils"
import { IdentityServiceError } from "@/components/MainArea/Graph/Identity/IdentityApi"
import type { CustomNodeData } from "../Elements/types"

/** OASF record from directory API; URL fields used for link in modal. */
export interface OasfRecord {
  /** Directory URL (snake_case from API). */
  directory_url?: string
  /** Directory URL (camelCase variant). */
  directoryUrl?: string
  url?: string
  [key: string]: unknown
}

const getSlugFromNodeData = (
  nodeData: CustomNodeData | null | undefined,
): string => {
  if (!nodeData) {
    throw new Error("nodeData is required for slug resolution")
  }
  if (nodeData.slug) {
    return nodeData.slug
  }

  console.log("Node data for slug extraction:", nodeData)

  const label1 = nodeData.label1?.toLowerCase()
  const label2 = nodeData.label2?.toLowerCase()

  if (label1 === "auction agent" || label2?.includes("buyer")) {
    return "auction-supervisor-agent"
  }

  if (label1 === "mcp server" && label2 === "weather") {
    return "weather-mcp-server"
  }

  if (label1 === "colombia" && label2?.includes("coffee farm")) {
    return "colombia-coffee-farm"
  }

  if (label1 === "vietnam" && label2?.includes("coffee farm")) {
    return "vietnam-coffee-farm"
  }

  if (label1 === "brazil" && label2?.includes("coffee farm")) {
    return "brazil-coffee-farm"
  }

  // Logistics
  if (label1 === "buyer" || label2?.includes("logistics agent")) {
    return "logistics-supervisor-agent"
  }

  if (label1 === "tatooine" && label2?.includes("coffee farm")) {
    return "tatooine-farm-agent"
  }

  if (label1 === "mcp server" && label2 === "payment") {
    return "payment-mcp-server"
  }

  if (label1 === "shipper") {
    return "shipping-agent"
  }

  if (label1 === "accountant") {
    return "accountant-agent"
  }

  throw new Error(`No valid slug mapping found for node: ${label1} ${label2}`)
}

/** Node data that may already include a cached OASF record. */
type NodeDataForOasf =
  | (CustomNodeData & { oasfRecord?: OasfRecord })
  | null
  | undefined

export const fetchOasfRecord = async (
  nodeData: NodeDataForOasf,
): Promise<OasfRecord> => {
  if (nodeData?.oasfRecord) {
    return nodeData.oasfRecord
  }

  const slug = getSlugFromNodeData(nodeData)

  let pattern: string = PATTERNS.PUBLISH_SUBSCRIBE
  if (
    slug === "logistics-supervisor-agent" ||
    slug === "tatooine-farm-agent" ||
    slug === "shipping-agent" ||
    slug === "accountant-agent"
  ) {
    pattern = PATTERNS.GROUP_COMMUNICATION
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

    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage =
        error.response?.data?.message ||
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
