/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { LUNGO_FRONTEND_URLS } from "@/urls"
import { transportGithubLink } from "@/utils/transportGithub"

describe("transportGithubLink", () => {
  it.each([
    {
      caseName: "SLIM regular transport",
      transport: "SLIM",
      isStreaming: false,
      expectedSuffix: LUNGO_FRONTEND_URLS.github.transports.regular.slim,
    },
    {
      caseName: "NATS streaming transport",
      transport: "NATS",
      isStreaming: true,
      expectedSuffix: LUNGO_FRONTEND_URLS.github.transports.streaming.nats,
    },
    {
      caseName: "unknown transport falls back to general",
      transport: "HTTP",
      isStreaming: false,
      expectedSuffix: LUNGO_FRONTEND_URLS.github.transports.general,
    },
  ])("$caseName", ({ transport, isStreaming, expectedSuffix }) => {
    const url = transportGithubLink(transport, isStreaming)
    expect(url).toBe(
      `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${expectedSuffix}`,
    )
  })
})
