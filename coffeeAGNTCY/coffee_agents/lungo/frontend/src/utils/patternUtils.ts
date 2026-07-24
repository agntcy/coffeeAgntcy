/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import {
  getDiscoveryAppApiUrl,
  getExchangeAppApiUrl,
  getLogisticsAppApiUrl,
} from "@/urls"

export const PATTERNS = {
  SLIM_A2A: "slim_a2a",
  PUBLISH_SUBSCRIBE: "publish_subscribe",
  PUBLISH_SUBSCRIBE_STREAMING: "publish_subscribe_streaming",
  GROUP_MESSAGING: "group_messaging",
  A2A_HTTP: "a2a_http",
} as const

export type PatternType = (typeof PATTERNS)[keyof typeof PATTERNS]

export type ChatApiTarget = "exchange" | "logistics" | "discovery"

/** Resolves the backend app URL for a workflow's `chat_api_target`. */
export const getApiUrlForChatTarget = (
  target?: ChatApiTarget | null,
): string => {
  if (target === "logistics") {
    return getLogisticsAppApiUrl()
  }
  if (target === "discovery") {
    return getDiscoveryAppApiUrl()
  }
  return getExchangeAppApiUrl()
}
