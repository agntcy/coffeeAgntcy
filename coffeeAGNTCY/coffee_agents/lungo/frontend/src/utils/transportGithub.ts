/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * GitHub browse URLs for deployment message transports (SLIM / NATS / general).
 */

import { LUNGO_FRONTEND_URLS } from "@/urls"

export function transportGithubLink(
  transport: string,
  isStreaming: boolean,
): string {
  const transportUrls = isStreaming
    ? LUNGO_FRONTEND_URLS.github.transports.streaming
    : LUNGO_FRONTEND_URLS.github.transports.regular
  if (transport === "SLIM") {
    return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.slim}`
  }
  if (transport === "NATS") {
    return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.nats}`
  }
  return `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.general}`
}
