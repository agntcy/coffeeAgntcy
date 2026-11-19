/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { ThemeProvider } from "@open-ui-kit/core"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import MermaidBlock from "./MermaidBlock"

let releaseRender: (svg: string) => void = () => {}

vi.mock("mermaid", () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(
      () =>
        new Promise<{ svg: string }>((resolve) => {
          releaseRender = (svg) => resolve({ svg })
        }),
    ),
  },
}))

const renderChart = (chart: string) =>
  render(
    <ThemeProvider>
      <MermaidBlock chart={chart} />
    </ThemeProvider>,
  )

describe("MermaidBlock", () => {
  it("clears the previous diagram when the chart changes", async () => {
    const { rerender } = renderChart("graph TD; A-->B")
    expect(screen.getByTestId("mermaid-loading")).toBeInTheDocument()

    releaseRender("<svg>first</svg>")
    await waitFor(() => {
      expect(screen.getByTestId("mermaid-svg")).toBeInTheDocument()
    })

    rerender(
      <ThemeProvider>
        <MermaidBlock chart="graph TD; C-->D" />
      </ThemeProvider>,
    )
    expect(screen.getByTestId("mermaid-loading")).toBeInTheDocument()
  })
})
