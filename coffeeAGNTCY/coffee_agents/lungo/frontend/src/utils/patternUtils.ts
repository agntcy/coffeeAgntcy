/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export const PATTERNS = {
  SLIM_A2A: "slim_a2a",
  PUBLISH_SUBSCRIBE: "publish_subscribe",
  PUBLISH_SUBSCRIBE_STREAMING: "publish_subscribe_streaming",
  GROUP_COMMUNICATION: "group_communication",
} as const

export type PatternType = (typeof PATTERNS)[keyof typeof PATTERNS]

export const isGroupCommunication = (pattern?: string): boolean => {
  return pattern === PATTERNS.GROUP_COMMUNICATION
}

export const shouldEnableRetries = (pattern?: string): boolean => {
  return isGroupCommunication(pattern)
}

export const getApiUrlForPattern = (pattern?: string): string => {
  const DEFAULT_PUB_SUB_API_URL = "http://127.0.0.1:8000"
  const DEFAULT_GROUP_COMM_APP_API_URL = "http://127.0.0.1:9090"

  const PUB_SUB_APP_API_URL =
    import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_PUB_SUB_API_URL
  const GROUP_COMM_APP_API_URL =
    import.meta.env.VITE_LOGISTICS_APP_API_URL || DEFAULT_GROUP_COMM_APP_API_URL

  if (isGroupCommunication(pattern)) {
    return GROUP_COMM_APP_API_URL
  } else if (pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
    return PUB_SUB_APP_API_URL
  } else {
    return PUB_SUB_APP_API_URL
  }
}

export const supportsSSE = (pattern?: string): boolean => {
  return isGroupCommunication(pattern)
}

export const getStreamingEndpointForPattern = (pattern?: string): string => {
  if (pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING) {
    return `${getApiUrlForPattern(pattern)}/agent/prompt/stream`
  }
  throw new Error(`Pattern ${pattern} does not support streaming`)
}

export const isStreamingPattern = (pattern?: string): boolean => {
  return pattern === PATTERNS.PUBLISH_SUBSCRIBE_STREAMING
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
    case PATTERNS.GROUP_COMMUNICATION:
      return "Group Communication"
    default:
      return "Unknown Pattern"
  }
}
