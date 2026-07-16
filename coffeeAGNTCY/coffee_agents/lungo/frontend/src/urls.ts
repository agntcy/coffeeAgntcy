/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Single source of truth for Lungo frontend URLs, env-backed config, and builders.
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

/** Relative API paths appended to pattern-specific or agentic-workflows bases. */
export type LungoFrontendApiPaths = {
  readonly about: "/about"
  readonly suggestedPrompts: "/suggested-prompts"
  readonly suggestedPromptsStreaming: "/suggested-prompts?pattern=streaming"
  readonly agentPrompt: "/agent/prompt"
  readonly agentPromptStream: "/agent/prompt/stream"
  readonly transportConfig: "/transport/config"
  readonly agenticWorkflowsCatalog: "/agentic-workflows/"
  readonly identityAppsBadge: (slug: string) => string
  readonly identityAppsPolicies: (slug: string) => string
  readonly agentsOasf: (slug: string) => string
  readonly agenticWorkflowsInstantiate: (workflowName: string) => string
  readonly agenticWorkflowsInstance: (
    workflowName: string,
    instanceUuid: string,
  ) => string
  readonly agenticWorkflowsInstanceSse: (
    workflowName: string,
    instanceUuid: string,
  ) => string
}

/** URLs, env-backed config, and static link catalogs for the Lungo frontend. */
export const LUNGO_FRONTEND_URLS = {
  urlDefaults: {
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

  urlEnvKeys: {
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
    about: "/about",
    suggestedPrompts: "/suggested-prompts",
    suggestedPromptsStreaming: "/suggested-prompts?pattern=streaming",
    agentPrompt: "/agent/prompt",
    agentPromptStream: "/agent/prompt/stream",
    transportConfig: "/transport/config",
    agenticWorkflowsCatalog: "/agentic-workflows/",
    identityAppsBadge: (slug: string): string => `/identity-apps/${slug}/badge`,
    identityAppsPolicies: (slug: string): string =>
      `/identity-apps/${slug}/policies`,
    agentsOasf: (slug: string): string => `/agents/${slug}/oasf`,
    agenticWorkflowsInstantiate: (workflowName: string): string => {
      const path = encodeWorkflowPathSegment(workflowName)
      return `/agentic-workflows/${path}/`
    },
    agenticWorkflowsInstance: (
      workflowName: string,
      instanceUuid: string,
    ): string => {
      const path = encodeWorkflowPathSegment(workflowName)
      return `/agentic-workflows/${path}/instances/${instanceUuid}/`
    },
    agenticWorkflowsInstanceSse: (
      workflowName: string,
      instanceUuid: string,
    ): string => {
      const path = encodeWorkflowPathSegment(workflowName)
      return `/agentic-workflows/${path}/instances/${instanceUuid}/events/stream`
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

type UrlDefaultKey = keyof typeof LUNGO_FRONTEND_URLS.urlDefaults
type ConfigDefaultKey = keyof typeof LUNGO_FRONTEND_URLS.configDefaults

function resolveUrlDefault(key: UrlDefaultKey): string {
  const envKey = LUNGO_FRONTEND_URLS.urlEnvKeys[key]
  return env.get(envKey) ?? LUNGO_FRONTEND_URLS.urlDefaults[key]
}

function resolveConfigDefault(key: ConfigDefaultKey): string {
  const envKey = LUNGO_FRONTEND_URLS.configEnvKeys[key]
  return env.get(envKey) ?? LUNGO_FRONTEND_URLS.configDefaults[key]
}

export function getExchangeAppApiUrl(): string {
  return resolveUrlDefault("exchangeAppApi")
}

export function getLogisticsAppApiUrl(): string {
  return resolveUrlDefault("logisticsAppApi")
}

export function getDiscoveryAppApiUrl(): string {
  return resolveUrlDefault("discoveryAppApi")
}

export function getAgenticWorkflowsApiUrl(): string {
  return resolveUrlDefault("agenticWorkflowsApi")
}

export function getGrafanaUrl(): string {
  return resolveUrlDefault("grafana")
}

export function getDirectoryServerUrl(): string {
  return resolveUrlDefault("directoryServer")
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

export function buildAgenticWorkflowsCatalogUrl(): string {
  return joinBaseUrl(
    getAgenticWorkflowsApiUrl(),
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsCatalog,
  )
}

export function buildWorkflowInstanceSseUrl(
  baseUrl: string,
  workflowName: string,
  instancePathUuid: string,
): string {
  return joinBaseUrl(
    baseUrl,
    LUNGO_FRONTEND_URLS.apiPaths.agenticWorkflowsInstanceSse(
      workflowName,
      instancePathUuid,
    ),
  )
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
