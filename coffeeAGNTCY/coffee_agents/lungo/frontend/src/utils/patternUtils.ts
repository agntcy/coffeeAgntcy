/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import {
  getDiscoveryAppApiUrl,
  getExchangeAppApiUrl,
  getLogisticsAppApiUrl,
  joinBaseUrl,
  LUNGO_FRONTEND_URLS,
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

export const isGroupCommunication = (pattern?: string): boolean => {
  return pattern === PATTERNS.GROUP_MESSAGING
}

export const shouldEnableRetries = (pattern?: string): boolean => {
  return isGroupCommunication(pattern)
}

export const getApiUrlForPattern = (pattern?: string): string => {
  if (isGroupCommunication(pattern)) {
    return getLogisticsAppApiUrl()
  }
  if (pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
    return getExchangeAppApiUrl()
  }
  if (pattern === PATTERNS.A2A_HTTP) {
    return getDiscoveryAppApiUrl()
  }
  return getExchangeAppApiUrl()
}

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

export const supportsSSE = (pattern?: string): boolean => {
  return isGroupCommunication(pattern)
}

export const getStreamingEndpointForPattern = (pattern?: string): string => {
  if (
    pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING ||
    pattern === PATTERNS.A2A_HTTP
  ) {
    return joinBaseUrl(
      getApiUrlForPattern(pattern),
      LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream,
    )
  }
  throw new Error(`Pattern ${pattern} does not support streaming`)
}

export const isStreamingPattern = (pattern?: string): boolean => {
  return (
    pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING ||
    pattern === PATTERNS.A2A_HTTP
  )
}

/** Patterns whose chat Send action must call `handleSendPrompt` (streaming handler). */
export const usesStreamingChatSend = (pattern?: string): boolean => {
  return (
    pattern === PATTERNS.GROUP_MESSAGING ||
    pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING ||
    pattern === PATTERNS.A2A_HTTP
  )
}

export const supportsTransportUpdates = (pattern?: string): boolean => {
  return (
    pattern === PATTERNS.PUBLISH_SUBSCRIBE ||
    pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING
  )
}

export const getPatternDisplayName = (pattern?: string): string => {
  switch (pattern) {
    case PATTERNS.SLIM_A2A:
      return "Slim A2A"
    case PATTERNS.PUBLISH_SUBSCRIBE:
      return "Publish/Subscribe"
    case PATTERNS.PUBLISH_SUBSCRIBE_STREAMING:
      return "Publish/Subscribe: Streaming"
    case PATTERNS.GROUP_MESSAGING:
      return "Group Messaging"
    case PATTERNS.A2A_HTTP:
      return "A2A HTTP"
    default:
      return "Unknown Pattern"
  }
}
