/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { render, screen } from "@testing-library/react"
import { ThemeProvider } from "@open-ui-kit/core"
import { describe, expect, it, vi } from "vitest"
import type { SidebarProps } from "./Sidebar"
import Sidebar from "./Sidebar"

const baseProps: SidebarProps = {
  selectedWorkflowSummary: null,
  summaries: [],
  patterns: [],
  patternsLoading: false,
  patternsError: null,
  patternCategories: [],
  patternCategoriesError: null,
  isLoading: false,
  error: null,
  onSelectWorkflow: vi.fn(),
}

const renderSidebar = (props: SidebarProps) =>
  render(
    <ThemeProvider>
      <Sidebar {...props} />
    </ThemeProvider>,
  )

describe("Sidebar independent catalog sources", () => {
  it("shows the reference library when the workflow catalog fails", async () => {
    renderSidebar({
      ...baseProps,
      error: "Workflow catalog unavailable",
      patterns: [
        {
          name: "Feedback Loop",
          pattern_category: "Learning, Feedback & Self-Improvement",
          implemented: false,
        },
      ],
    })

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Workflow catalog unavailable",
    )
    expect(await screen.findByText("Reference Library")).toBeInTheDocument()
    expect(await screen.findByText("Feedback Loop")).toBeInTheDocument()
  })

  it("does not show a false empty state while patterns are loading", () => {
    const { rerender } = renderSidebar({
      ...baseProps,
      patterns: null,
      patternsLoading: true,
    })

    expect(
      screen.getByText("Loading pattern reference library..."),
    ).toBeInTheDocument()
    expect(
      screen.queryByText("No workflows or patterns available"),
    ).not.toBeInTheDocument()

    rerender(
      <ThemeProvider>
        <Sidebar {...baseProps} />
      </ThemeProvider>,
    )

    expect(
      screen.getByText("No workflows or patterns available"),
    ).toBeInTheDocument()
  })
})
