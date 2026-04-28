/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_EXCHANGE_APP_API_URL?: string
  readonly VITE_LOGISTICS_APP_API_URL?: string
  readonly VITE_GRAFANA_URL?: string
  readonly VITE_DISCOVERY_APP_API_URL?: string
  readonly VITE_AGENTIC_WORKFLOWS_API_URL?: string
  readonly VITE_DIRECTORY_SERVER_URL?: string
  readonly VITE_DIRECTORY_VERSION?: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
  readonly BASE_URL: string
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
