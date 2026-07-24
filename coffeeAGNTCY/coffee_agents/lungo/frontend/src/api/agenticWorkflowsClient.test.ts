/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import type { EventV1Wire } from "@/api/agenticWorkflowsTypes"
import {
  parseSseDataLine,
  parseSseFrameLines,
  splitSseFrames,
} from "@/api/http/sseParsing"

describe("agenticWorkflowsClient SSE parsing", () => {
  it.each([
    {
      caseName: "splits complete frames and keeps remainder",
      input: 'data: {"a":1}\n\npartial',
      expectedFrames: ['data: {"a":1}'],
      expectedRemainder: "partial",
    },
    {
      caseName: "handles multiple frames",
      input: 'data: {"a":1}\n\n:\n\ndata: {"b":2}\n\n',
      expectedFrames: ['data: {"a":1}', ":", 'data: {"b":2}'],
      expectedRemainder: "",
    },
    {
      caseName: "no delimiter yields no frames",
      input: 'data: {"a":1}',
      expectedFrames: [],
      expectedRemainder: 'data: {"a":1}',
    },
  ])("$caseName", ({ input, expectedFrames, expectedRemainder }) => {
    const { frames, remainder } = splitSseFrames(input)
    expect(frames).toEqual(expectedFrames)
    expect(remainder).toBe(expectedRemainder)
  })

  it.each([
    {
      caseName: "parses a single data line",
      line: 'data: {"metadata":{"id":"event://1"},"data":{}}',
      ok: true,
    },
    {
      caseName: "ignores comment line",
      line: ":",
      ok: false,
    },
    {
      caseName: "ignores non-data line",
      line: "event: foo",
      ok: false,
    },
    {
      caseName: "ignores invalid json",
      line: "data: {not-json}",
      ok: false,
    },
  ])("$caseName", ({ line, ok }) => {
    const ev = parseSseDataLine<EventV1Wire>(line)
    expect(Boolean(ev)).toBe(ok)
  })

  it("frame parsing ignores comment and invalid data lines", () => {
    const frame = [
      ":",
      'data: {"metadata":{"id":"event://ok"},"data":{}}',
      "data: {not-json}",
      "",
    ].join("\n")
    const events = parseSseFrameLines<EventV1Wire>(frame)
    expect(events.length).toBe(1)
    expect(events[0]?.metadata?.id).toBeDefined()
  })
})
