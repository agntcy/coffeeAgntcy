/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import axios from "axios"
import { logger } from "@/utils/logger"

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL

/** OASF record from backend API; displayed inline in modal. */
export interface OasfRecord {
  name?: string
  description?: string
  [key: string]: unknown
}

export interface CustomNodeDataForSlug {
  slug?: string
  label1?: string
  label2?: string
}

const getSlugFromNodeData = (
  nodeData: CustomNodeDataForSlug | null | undefined
): string => {
  if (!nodeData) {
    throw new Error("nodeData is required for slug resolution")
  }
  if (nodeData.slug) {
    return nodeData.slug
  }
  const label1 = nodeData.label1?.toLowerCase()
  const label2 = nodeData.label2?.toLowerCase()
  if (
    label1 === "supervisor agent" ||
    (label2 && label2.includes("buyer"))
  ) {
    return "exchange-supervisor-agent"
  }
  if (
    label1 === "grader agent" ||
    (label2 && label2.includes("sommelier"))
  ) {
    return "flavor-profile-farm-agent"
  }
  throw new Error(`No valid slug mapping found for node: ${label1} ${label2}`)
}

export type NodeDataForOasf = CustomNodeDataForSlug & { oasfRecord?: OasfRecord }

export interface OasfApiError {
  message: string
  status?: number
}

export const fetchOasfRecord = async (
  nodeData: NodeDataForOasf | null | undefined
): Promise<OasfRecord> => {
  if (nodeData?.oasfRecord) {
    return nodeData.oasfRecord
  }
  const slug = getSlugFromNodeData(nodeData)
  try {
    const response = await axios.get<OasfRecord>(
      `${EXCHANGE_APP_API_URL}/agents/${slug}/oasf`,
      {
        timeout: 10000,
        headers: { "Content-Type": "application/json" },
      }
    )
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMessage =
        (error.response?.data as { detail?: string })?.detail ||
        error.message ||
        "Failed to fetch OASF record"
      logger.debug("OASF fetch error", { status: error.response?.status, errorMessage })
      throw { message: errorMessage, status: error.response?.status } as OasfApiError
    }
    throw {
      message: "An unexpected error occurred while fetching OASF record",
    } as OasfApiError
  }
}

export { getSlugFromNodeData }
