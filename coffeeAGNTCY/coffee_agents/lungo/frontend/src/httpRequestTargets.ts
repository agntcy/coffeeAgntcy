/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Assembled HTTP fetch URLs paired with endpointLabel metadata.
 * Paths and bases are defined in `@/urls`; this module joins them.
 **/

import {
  getAgenticWorkflowsApiUrl,
  getDiscoveryAppApiUrl,
  getExchangeAppApiUrl,
  getLogisticsAppApiUrl,
  getApiBaseForPattern,
  joinHttpRequest,
  LUNGO_FRONTEND_URLS,
  type HttpRequestTarget,
} from "@/urls"

function normalizeAgenticWorkflowsBase(baseUrl?: string): string {
  return (baseUrl ?? getAgenticWorkflowsApiUrl()).replace(/\/$/, "")
}

export function buildAboutRequest(): HttpRequestTarget {
  return joinHttpRequest(
    getExchangeAppApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.about,
  )
}

export function buildAgentPromptRequest(pattern?: string): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseForPattern(pattern),
    LUNGO_FRONTEND_URLS.apiPaths.agentPrompt,
  )
}

export function buildAgentPromptStreamRequest(
  pattern?: string,
): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseForPattern(pattern),
    LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream,
  )
}

export function buildGroupAgentPromptStreamRequest(): HttpRequestTarget {
  return joinHttpRequest(
    getLogisticsAppApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.agentPromptStream,
  )
}

export function buildTransportConfigRequest(
  pattern?: string,
): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseForPattern(pattern),
    LUNGO_FRONTEND_URLS.apiPaths.transportConfig,
  )
}

export function buildIdentityBadgeRequest(slug: string): HttpRequestTarget {
  return joinHttpRequest(
    getExchangeAppApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.identityAppsBadge(slug),
  )
}

export function buildIdentityPolicyRequest(slug: string): HttpRequestTarget {
  return joinHttpRequest(
    getExchangeAppApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.identityAppsPolicies(slug),
  )
}

export function buildAgentsOasfRequest(
  slug: string,
  pattern?: string,
): HttpRequestTarget {
  return joinHttpRequest(
    getApiBaseForPattern(pattern),
    LUNGO_FRONTEND_URLS.apiPaths.agentsOasf(slug),
  )
}

export type SuggestedPromptsSource = "coffee" | "logistics" | "discovery"

export function buildSuggestedPromptsRequest(
  source: SuggestedPromptsSource,
  pattern?: string,
): HttpRequestTarget {
  switch (source) {
    case "coffee": {
      const route =
        pattern === "publish_subscribe_streaming"
          ? LUNGO_FRONTEND_URLS.apiPaths.suggestedPromptsStreaming
          : LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts
      return joinHttpRequest(getExchangeAppApiUrl(), route)
    }
    case "logistics":
      return joinHttpRequest(
        getLogisticsAppApiUrl(),
        LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts,
      )
    case "discovery":
      return joinHttpRequest(
        getDiscoveryAppApiUrl(),
        LUNGO_FRONTEND_URLS.apiPaths.suggestedPrompts,
      )
  }
}

export function buildAgenticWorkflowsCatalogRequest(): HttpRequestTarget {
  return joinHttpRequest(
    getAgenticWorkflowsApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsCatalog,
  )
}

export function buildAgenticWorkflowsDocumentationRequest(
  workflowName: string,
): HttpRequestTarget {
  return joinHttpRequest(
    getAgenticWorkflowsApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsDocumentation(workflowName),
  )
}

export function buildAgenticWorkflowsInstantiateRequest(
  workflowName: string,
  baseUrl?: string,
): HttpRequestTarget {
  return joinHttpRequest(
    normalizeAgenticWorkflowsBase(baseUrl),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstantiate(workflowName),
  )
}

export function buildAgenticWorkflowsInstanceRequest(
  workflowName: string,
  instanceUuid: string,
  options?: { baseUrl?: string; topologyOnly?: boolean },
): HttpRequestTarget {
  return joinHttpRequest(
    normalizeAgenticWorkflowsBase(options?.baseUrl),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstance(
      workflowName,
      instanceUuid,
    ),
    options?.topologyOnly ? { topology_only: "true" } : undefined,
  )
}

export function buildAgenticWorkflowsInstanceSseRequest(
  workflowName: string,
  instancePathUuid: string,
  baseUrl?: string,
): HttpRequestTarget {
  return joinHttpRequest(
    normalizeAgenticWorkflowsBase(baseUrl),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstanceSse(
      workflowName,
      instancePathUuid,
    ),
  )
}

export function buildAgenticWorkflowsCatalogUrl(): string {
  return buildAgenticWorkflowsCatalogRequest().url
}

export function buildWorkflowInstanceSseUrl(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
): string {
  return buildAgenticWorkflowsInstanceSseRequest(
    workflowName,
    instancePathUuid,
    baseUrl,
  ).url
}
