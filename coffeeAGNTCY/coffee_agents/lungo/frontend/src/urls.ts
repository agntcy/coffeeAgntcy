/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Single source of truth for Lungo frontend HTTP configuration: API base URLs,
 * relative paths (with endpointLabel), assembled fetch URLs, and static link catalogs.
 * Import via `@/urls`.
 **/

import { env } from "@/utils/env"

export function encodeWorkflowPathSegment(workflowName: string): string {
  return encodeURIComponent(workflowName)
}

/** Join a base URL with a path segment (path must start with `/`). */
export function joinBaseUrl(base: string, path: string): string {
  return `${base.replace(/\/$/, "")}${path}`
}

/** Relative API route: path joins to a base URL; endpointLabel is for logs and HttpError metadata. */
export type ApiRoute = {
  readonly path: string
  readonly endpointLabel: string
}

export function apiRoute(path: string, endpointLabel: string = path): ApiRoute {
  return { path, endpointLabel }
}

/**
 * Logical endpoint labels live at feature/UI boundaries and are intentionally
 * **not** entries in `apiPaths` below. Each maps to one or more apiPaths calls,
 * but names the user-facing workflow or surface for logs, HttpError metadata,
 * and `reportRequestError`.
 *
 * - `agentic-workflows/bootstrap` — `useWorkflowGraphAgenticBootstrap.ts`
 *   Covers instantiate + topology fetch + SSE attach in one catch; no single
 *   apiPath describes that composite flow.
 * - `agentic-workflows/sse` — `useWorkflowGraphAgenticBootstrap.ts`
 *   SSE reconnect exhaustion after repeated stream failures.
 * - `agentic-workflows/refetch-topology` — `useWorkflowGraphTopologySync.ts`
 *   Topology refetch exhaustion after debounced retries.
 * - `identity/badge-details` — `BadgeDetailsModal.tsx`
 *   Modal-level reporting; HTTP traffic uses `identityAppsBadge(slug)`.
 * - `identity/policy-details` — `PolicyDetailsModal.tsx`
 *   Modal-level reporting; HTTP traffic uses `identityAppsPolicies(slug)`.
 * - `directory/oasf-record` — `OasfRecordModal.tsx`
 *   Modal-level reporting; HTTP traffic uses `agentsOasf(slug)`.
 */

/** Relative API paths appended to pattern-specific or agentic-workflows bases. */
export type LungoFrontendApiPaths = {
  readonly about: ApiRoute
  readonly suggestedPrompts: ApiRoute
  readonly suggestedPromptsStreaming: ApiRoute
  readonly agentPrompt: ApiRoute
  readonly agentPromptStream: ApiRoute
  readonly transportConfig: ApiRoute
  readonly agenticWorkflowsCatalog: ApiRoute
  readonly identityAppsBadge: (slug: string) => ApiRoute
  readonly identityAppsPolicies: (slug: string) => ApiRoute
  readonly agentsOasf: (slug: string) => ApiRoute
  readonly agenticWorkflowsInstantiate: (workflowName: string) => ApiRoute
  readonly agenticWorkflowsInstance: (
    workflowName: string,
    instanceUuid: string,
  ) => ApiRoute
  readonly agenticWorkflowsInstanceSse: (
    workflowName: string,
    instanceUuid: string,
  ) => ApiRoute
  readonly agenticWorkflowsDocumentation: (workflowName: string) => ApiRoute
}

/** URLs, env-backed config, and static link catalogs for the Lungo frontend. */
export const LUNGO_FRONTEND_URLS = {
  /** Env-backed API host roots (scheme + host + port). */
  apiBaseDefaults: {
    exchangeAppApi: "http://127.0.0.1:8000",
    logisticsAppApi: "http://127.0.0.1:9090",
    discoveryAppApi: "http://127.0.0.1:8882",
    agenticWorkflowsApi: "http://127.0.0.1:9105",
    grafana: "http://127.0.0.1:3001",
    directoryServer: "http://127.0.0.1:8888",
  } as const,

  /** Non-URL values resolved from Vite env (version labels, branch names, etc.). */
  configDefaults: {
    directoryVersion: "v1.0.0",
    agenticWorkflowsDocsGithubBranch: "main",
  } as const,

  apiBaseEnvKeys: {
    exchangeAppApi: "VITE_EXCHANGE_APP_API_URL",
    logisticsAppApi: "VITE_LOGISTICS_APP_API_URL",
    discoveryAppApi: "VITE_DISCOVERY_APP_API_URL",
    agenticWorkflowsApi: "VITE_AGENTIC_WORKFLOWS_API_URL",
    grafana: "VITE_GRAFANA_URL",
    directoryServer: "VITE_DIRECTORY_SERVER_URL",
  } as const,

  configEnvKeys: {
    directoryVersion: "VITE_DIRECTORY_VERSION",
    agenticWorkflowsDocsGithubBranch:
      "VITE_AGENTIC_WORKFLOWS_DOCS_GITHUB_BRANCH",
  } as const,

  secretEnvKeys: {
    agenticWorkflowsApiKey: "VITE_AGENTIC_WORKFLOWS_API_KEY",
  } as const,

  paths: {
    grafanaDashboardPrefix:
      "/d/lungo-dashboard/lungo-dashboard?orgId=1&var-session_id=",
  } as const,

  apiPaths: {
    about: apiRoute("/about"),
    suggestedPrompts: apiRoute("/suggested-prompts"),
    suggestedPromptsStreaming: apiRoute("/suggested-prompts?pattern=streaming"),
    agentPrompt: apiRoute("/agent/prompt"),
    agentPromptStream: apiRoute("/agent/prompt/stream"),
    transportConfig: apiRoute("/transport/config"),
    agenticWorkflowsCatalog: apiRoute("/agentic-workflows/"),
    identityAppsBadge: (slug: string): ApiRoute =>
      apiRoute(`/identity-apps/${slug}/badge`),
    identityAppsPolicies: (slug: string): ApiRoute =>
      apiRoute(`/identity-apps/${slug}/policies`),
    agentsOasf: (slug: string): ApiRoute => apiRoute(`/agents/${slug}/oasf`),
    agenticWorkflowsInstantiate: (workflowName: string): ApiRoute => {
      const path = encodeWorkflowPathSegment(workflowName)
      return apiRoute(`/agentic-workflows/${path}/`)
    },
    agenticWorkflowsInstance: (
      workflowName: string,
      instanceUuid: string,
    ): ApiRoute => {
      const path = encodeWorkflowPathSegment(workflowName)
      return apiRoute(`/agentic-workflows/${path}/instances/${instanceUuid}/`)
    },
    agenticWorkflowsInstanceSse: (
      workflowName: string,
      instanceUuid: string,
    ): ApiRoute => {
      const path = encodeWorkflowPathSegment(workflowName)
      return apiRoute(
        `/agentic-workflows/${path}/instances/${instanceUuid}/events/stream`,
      )
    },
    agenticWorkflowsDocumentation: (workflowName: string): ApiRoute => {
      const path = encodeWorkflowPathSegment(workflowName)
      return apiRoute(`/agentic-workflows/${path}/documentation/`)
    },
  } satisfies LungoFrontendApiPaths,

  workflowDocumentation: {
    githubRepoBlobRoot: "https://github.com/agntcy/coffeeAgntcy/blob",
    docsWorkflowsPath:
      "coffeeAGNTCY/coffee_agents/lungo/api/agentic_workflows/docs/workflows",
  } as const,

  github: {
    baseUrl:
      "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents",
    appSdkBaseUrl:
      "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk",
    agents: {
      supervisorAuction:
        "/lungo/agents/supervisors/auction/graph/graph.py#L451",
      supervisorAuctionStreaming:
        "/lungo/agents/supervisors/auction/graph/graph.py#L511",
      brazilFarm: "/lungo/agents/farms/brazil/agent.py#L32",
      brazilFarmStreaming: "/lungo/agents/farms/brazil/agent.py#L193",
      colombiaFarm: "/lungo/agents/farms/colombia/agent.py#L55",
      colombiaFarmStreaming: "/lungo/agents/farms/colombia/agent.py#L287",
      vietnamFarm: "/lungo/agents/farms/vietnam/agent.py#L32",
      vietnamFarmStreaming: "/lungo/agents/farms/vietnam/agent.py#L192",
      weatherMcp: "/lungo/agents/mcp_servers/weather_service.py#L24",
      paymentMcp: "/lungo/agents/mcp_servers/payment_service.py",
      logisticSupervisor:
        "/lungo/agents/supervisors/logistic/graph/tools.py#L150",
      logisticFarm: "/lungo/agents/logistics/farm/agent_executor.py#L42",
      logisticShipper: "/lungo/agents/logistics/shipper/agent_executor.py#L41",
      logisticAccountant:
        "/lungo/agents/logistics/accountant/agent_executor.py#L42",
      recruiter: "/lungo/agents/recruiter/agent.py#L32",
    },
    transports: {
      general: "/tree/main/src/agntcy_app_sdk/transports",
      group: "/transport/slim/transport.py#L294",
      regular: {
        slim: "/transport/slim/transport.py#L176",
        nats: "/transport/nats/transport.py#L119",
      },
      streaming: {
        slim: "/transport/slim/transport.py#L203",
        nats: "/transport/nats/transport.py#L147",
      },
    },
  },

  identity: {
    colombia:
      "https://github.com/agntcy/app-sdk/blob/v0.4.4-dev.1/src/agntcy_app_sdk/semantic/a2a/protocol.py#L256-L272",
    auction:
      "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/semantic/a2a/protocol.py#L195-L201",
    payment:
      "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/semantic/fast_mcp/protocol.py#L72-L74",
  },

  agentDirectory: {
    baseUrl: "https://agent-directory.outshift.com/explore",
    github: "https://github.com/agntcy/dir",
  },
} as const

type ApiBaseDefaultKey = keyof typeof LUNGO_FRONTEND_URLS.apiBaseDefaults
type ConfigDefaultKey = keyof typeof LUNGO_FRONTEND_URLS.configDefaults

function resolveApiBaseDefault(key: ApiBaseDefaultKey): string {
  const envKey = LUNGO_FRONTEND_URLS.apiBaseEnvKeys[key]
  return env.get(envKey) ?? LUNGO_FRONTEND_URLS.apiBaseDefaults[key]
}

function resolveConfigDefault(key: ConfigDefaultKey): string {
  const envKey = LUNGO_FRONTEND_URLS.configEnvKeys[key]
  return env.get(envKey) ?? LUNGO_FRONTEND_URLS.configDefaults[key]
}

export function getExchangeAppApiUrl(): string {
  return resolveApiBaseDefault("exchangeAppApi")
}

export function getLogisticsAppApiUrl(): string {
  return resolveApiBaseDefault("logisticsAppApi")
}

export function getDiscoveryAppApiUrl(): string {
  return resolveApiBaseDefault("discoveryAppApi")
}

export function getAgenticWorkflowsApiUrl(): string {
  return resolveApiBaseDefault("agenticWorkflowsApi")
}

export function getGrafanaUrl(): string {
  return resolveApiBaseDefault("grafana")
}

export function getDirectoryServerUrl(): string {
  return resolveApiBaseDefault("directoryServer")
}

export function getDirectoryVersion(): string {
  return resolveConfigDefault("directoryVersion")
}

export function getAgenticWorkflowsDocsGithubBranch(): string {
  return resolveConfigDefault("agenticWorkflowsDocsGithubBranch")
}

export function getAgenticWorkflowsApiKey(): string {
  return env.get(LUNGO_FRONTEND_URLS.secretEnvKeys.agenticWorkflowsApiKey) ?? ""
}

/** Assembled HTTP fetch target: full URL plus stable endpointLabel for errors/logs. */
export type HttpRequestTarget = {
  readonly url: string
  readonly endpointLabel: string
}

export function joinHttpRequest(
  base: string,
  route: ApiRoute,
  query?: Record<string, string>,
): HttpRequestTarget {
  let url = joinBaseUrl(base.replace(/\/$/, ""), route.path)
  if (query && Object.keys(query).length > 0) {
    const qs = new URLSearchParams(query).toString()
    url += `${url.includes("?") ? "&" : "?"}${qs}`
  }
  return { url, endpointLabel: route.endpointLabel }
}

/** Pick the pattern-app API host for agent/chat/transport requests. */
export function getApiBaseForPattern(pattern?: string): string {
  if (pattern === "group_messaging") {
    return getLogisticsAppApiUrl()
  }
  if (pattern === "publish_subscribe_streaming") {
    return getExchangeAppApiUrl()
  }
  if (pattern === "a2a_http") {
    return getDiscoveryAppApiUrl()
  }
  return getExchangeAppApiUrl()
}

export function buildGrafanaSessionDashboardUrl(sessionId: string): string {
  return `${getGrafanaUrl()}${LUNGO_FRONTEND_URLS.paths.grafanaDashboardPrefix}${encodeURIComponent(sessionId)}`
}

/** Map catalog display name to markdown basename (without `.md`). */
export function workflowNameToDocumentationSlug(name: string): string {
  let s = name.trim().toLowerCase()
  s = s.replace(/[\u2013\u2014\u2212]/g, "_")
  s = s.replace(/ /g, "_")
  s = s.replace(/[()]/g, "_")
  s = s.replace(/_+/g, "_")
  return s.replace(/^_|_$/g, "")
}

export function getWorkflowDocumentationGithubUrl(catalogName: string): string {
  const branch = getAgenticWorkflowsDocsGithubBranch()
  const slug = workflowNameToDocumentationSlug(catalogName)
  const branchSegment = encodeURIComponent(branch)
  const { githubRepoBlobRoot, docsWorkflowsPath } =
    LUNGO_FRONTEND_URLS.workflowDocumentation
  return `${githubRepoBlobRoot}/${branchSegment}/${docsWorkflowsPath}/${slug}.md`
}

export {
  buildAboutRequest,
  buildAgentPromptRequest,
  buildAgentPromptStreamRequest,
  buildAgenticWorkflowsCatalogRequest,
  buildAgenticWorkflowsCatalogUrl,
  buildAgenticWorkflowsDocumentationRequest,
  buildAgenticWorkflowsInstantiateRequest,
  buildAgenticWorkflowsInstanceRequest,
  buildAgenticWorkflowsInstanceSseRequest,
  buildAgentsOasfRequest,
  buildGroupAgentPromptStreamRequest,
  buildIdentityBadgeRequest,
  buildIdentityPolicyRequest,
  buildSuggestedPromptsRequest,
  buildTransportConfigRequest,
  buildWorkflowInstanceSseUrl,
  type SuggestedPromptsSource,
} from "./httpRequestTargets.ts"
