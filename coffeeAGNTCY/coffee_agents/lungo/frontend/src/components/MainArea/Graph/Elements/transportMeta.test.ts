/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { OasfRecord } from "../Directory/DirectoryApi"
import { extractA2aTransportsFromOasf, transportMetaFor } from "./transportMeta"

describe("transportMeta", () => {
  it("extracts camel-case A2A additional interfaces from OASF records", () => {
    const record = {
      modules: [
        {
          name: "integration/a2a",
          data: {
            card_data: {
              preferredTransport: "slimrpc",
              additionalInterfaces: [
                {
                  transport: "slimrpc",
                  url: "slim://slim:46357/lungo/agents/brazil",
                },
                {
                  transport: "slim",
                  url: "slim://slim:46357/lungo/agents/brazil",
                },
                {
                  transport: "nats",
                  url: "nats://nats:4222/lungo/agents/brazil",
                },
                {
                  transport: "jsonrpc",
                  url: "http://0.0.0.0:9999",
                },
              ],
            },
          },
        },
      ],
    } satisfies OasfRecord

    expect(extractA2aTransportsFromOasf(record)).toEqual([
      {
        name: "slimrpc",
        url: "slim://slim:46357/lungo/agents/brazil",
        preferred: true,
      },
      {
        name: "slim",
        url: "slim://slim:46357/lungo/agents/brazil",
        preferred: false,
      },
      {
        name: "nats",
        url: "nats://nats:4222/lungo/agents/brazil",
        preferred: false,
      },
      {
        name: "jsonrpc",
        url: "http://0.0.0.0:9999",
        preferred: false,
      },
    ])
  })

  it("supports snake-case A2A card fields", () => {
    const record = {
      modules: [
        {
          data: {
            card_data: {
              preferred_transport: "slim",
              additional_interfaces: [
                { transport: "slim" },
                { transport: "slimrpc" },
              ],
            },
          },
        },
      ],
    } satisfies OasfRecord

    expect(extractA2aTransportsFromOasf(record)).toEqual([
      { name: "slim", url: undefined, preferred: true },
      { name: "slimrpc", url: undefined, preferred: false },
    ])
  })

  it("returns an empty list for records without A2A interfaces", () => {
    expect(extractA2aTransportsFromOasf({ modules: [] })).toEqual([])
    expect(
      extractA2aTransportsFromOasf({
        modules: [{ data: { card_data: { additionalInterfaces: null } } }],
      }),
    ).toEqual([])
  })

  it("provides a fallback display meta for unknown transports", () => {
    expect(transportMetaFor("custombus")).toMatchObject({
      short: "CUSTOMBUS",
      label: "Additional agent interface",
    })
  })
})
