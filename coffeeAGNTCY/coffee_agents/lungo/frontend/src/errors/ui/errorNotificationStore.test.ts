/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { beforeEach, describe, expect, it } from "vitest"
import { useErrorNotificationStore } from "./errorNotificationStore"

describe("useErrorNotificationStore", () => {
  beforeEach(() => {
    useErrorNotificationStore.setState({ notifications: [] })
  })

  it("queues a notification with pushError", () => {
    const id = useErrorNotificationStore.getState().pushError({
      title: "Request failed",
      message: "Menu is unavailable",
      source: "/api/catalog",
    })

    const notifications = useErrorNotificationStore.getState().notifications
    expect(notifications).toHaveLength(1)
    expect(notifications[0]).toMatchObject({
      id,
      severity: "error",
      title: "Request failed",
      message: "Menu is unavailable",
      source: "/api/catalog",
    })
  })

  it("dismisses a notification by id", () => {
    const { pushError, dismissError } = useErrorNotificationStore.getState()
    const id = pushError({
      title: "Request failed",
      message: "One",
    })
    pushError({
      title: "Request failed",
      message: "Two",
    })

    dismissError(id)

    expect(useErrorNotificationStore.getState().notifications).toHaveLength(1)
    expect(useErrorNotificationStore.getState().notifications[0]?.message).toBe(
      "Two",
    )
  })

  it("clears all notifications", () => {
    const { pushError, clearAll } = useErrorNotificationStore.getState()
    pushError({ title: "A", message: "One" })
    pushError({ title: "B", message: "Two" })

    clearAll()

    expect(useErrorNotificationStore.getState().notifications).toEqual([])
  })
})
