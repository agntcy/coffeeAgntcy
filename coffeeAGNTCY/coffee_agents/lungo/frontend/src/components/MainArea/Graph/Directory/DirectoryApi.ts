/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { fetchJson } from "@/api/http"
import { buildAgentsOasfRequest } from "@/urls"
import { type ChatApiTarget } from "@/utils/patternUtils"
import type { CustomNodeData } from "../Elements/types"
import { getOasfSlugFromNodeData } from "@/utils/agenticTopologyIdentityUiMap"

const DIRECTORY_REQUEST_TIMEOUT_MS = 10_000

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

function oasfCacheKey(target: ChatApiTarget, slug: string): string {
  return `${target}\0${slug}`
}

export const fetchOasfRecord = async (
  nodeData: NodeDataForOasf,
  chatApiTarget?: ChatApiTarget | null,
): Promise<OasfRecord> => {
  if (nodeData?.oasfRecord) {
    return nodeData.oasfRecord
  }

  const slug = getOasfSlugFromNodeData(nodeData)
  const target: ChatApiTarget = chatApiTarget ?? "exchange"

  const cacheKey = oasfCacheKey(target, slug)
  const cached = oasfFetchCache.get(cacheKey)
  if (cached) {
    return cached
  }

  const request = buildAgentsOasfRequest(slug, target)
  const record = await fetchJson<OasfRecord>(request.url, {
    endpointLabel: request.endpointLabel,
    timeoutMs: DIRECTORY_REQUEST_TIMEOUT_MS,
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (oasfFetchCache.size >= OASF_FETCH_CACHE_MAX) {
    const first = oasfFetchCache.keys().next().value
    if (first !== undefined) oasfFetchCache.delete(first)
  }
  oasfFetchCache.set(cacheKey, record)

  return record
}
