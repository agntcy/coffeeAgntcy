/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"
import ErrorNotifications from "./ErrorNotifications"
import { useErrorNotificationStore } from "./errorNotificationStore"

const renderNotifications = () =>
  render(
    <ThemeProvider>
      <ErrorNotifications />
    </ThemeProvider>,
  )

describe("ErrorNotifications", () => {
  beforeEach(() => {
    useErrorNotificationStore.setState({ notifications: [] })
  })

  it("renders nothing when the queue is empty", () => {
    const { container } = renderNotifications()
    expect(container).toBeEmptyDOMElement()
  })

  it("renders queued notifications with alert semantics", () => {
    useErrorNotificationStore.setState({
      notifications: [
        {
          id: "n1",
          severity: "error",
          title: "Request failed",
          message: "Menu is unavailable",
          source: "/api/catalog",
        },
      ],
    })

    renderNotifications()

    expect(
      screen.getByRole("region", { name: "Application notifications" }),
    ).toBeInTheDocument()
    expect(screen.getByRole("alert")).toHaveTextContent("Request failed")
    expect(screen.getByRole("alert")).toHaveTextContent("Menu is unavailable")
  })

  it("dismisses a notification when the close button is clicked", () => {
    useErrorNotificationStore.setState({
      notifications: [
        {
          id: "n1",
          severity: "warning",
          title: "Warning",
          message: "Topology is stale",
        },
      ],
    })

    renderNotifications()

    fireEvent.click(screen.getByRole("button", { name: "close" }))

    expect(useErrorNotificationStore.getState().notifications).toEqual([])
    expect(screen.queryByRole("alert")).not.toBeInTheDocument()
  })
})
