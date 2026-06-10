/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it } from "vitest"
import { buildPromptRequestBody } from "@/hooks/useAgentAPI"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"

describe("buildPromptRequestBody", () => {
  afterEach(() => {
    useActiveWorkflowInstanceStore.getState().setWorkflowInstanceId(null)
  })

  it("tags the request with the active workflow instance id so the events SSE receives animations in non-streaming mode", () => {
    useActiveWorkflowInstanceStore
      .getState()
      .setWorkflowInstanceId("instance://abc-123")

    expect(buildPromptRequestBody("hello")).toEqual({
      prompt: "hello",
      workflow_instance_id: "instance://abc-123",
    })
  })

  it("omits workflow_instance_id when no workflow instance is active", () => {
    expect(buildPromptRequestBody("hello")).toEqual({ prompt: "hello" })
    expect(buildPromptRequestBody("hello")).not.toHaveProperty(
      "workflow_instance_id",
    )
  })
})
