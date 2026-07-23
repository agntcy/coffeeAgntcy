/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import {
  getDiscoveryAppApiUrl,
  getExchangeAppApiUrl,
  getLogisticsAppApiUrl,
} from "@/urls"
import {
  getApiUrlForChatTarget,
  type ChatApiTarget,
} from "@/utils/patternUtils"

describe("getApiUrlForChatTarget", () => {
  it.each([
    {
      caseName: "logistics target resolves to logistics app",
      target: "logistics" as ChatApiTarget,
      expected: getLogisticsAppApiUrl(),
    },
    {
      caseName: "discovery target resolves to discovery app",
      target: "discovery" as ChatApiTarget,
      expected: getDiscoveryAppApiUrl(),
    },
    {
      caseName: "exchange target resolves to exchange app",
      target: "exchange" as ChatApiTarget,
      expected: getExchangeAppApiUrl(),
    },
    {
      caseName: "null defaults to exchange app",
      target: null,
      expected: getExchangeAppApiUrl(),
    },
    {
      caseName: "undefined defaults to exchange app",
      target: undefined,
      expected: getExchangeAppApiUrl(),
    },
  ])("$caseName", ({ target, expected }) => {
    expect(getApiUrlForChatTarget(target)).toBe(expected)
  })
})
