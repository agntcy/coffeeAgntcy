/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { describe, expect, it } from "vitest"
import { renderHook } from "@testing-library/react"
import { useAppStreamingState } from "./useAppStreamingState"

describe("useAppStreamingState", () => {
  it("renders without a selector update loop", () => {
    expect(() => renderHook(() => useAppStreamingState())).not.toThrow()
  })
})
