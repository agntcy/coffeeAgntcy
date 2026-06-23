/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import PatternDocMarkdown from "./PatternDocMarkdown"

const mockRender = vi.fn()

vi.mock("mermaid", () => ({
  default: {
    initialize: vi.fn(),
    render: (id: string, code: string) => mockRender(id, code),
  },
}))

vi.mock("@/utils/logger", () => ({
  logger: {
    error: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    apiError: vi.fn(),
  },
}))

beforeEach(() => {
  mockRender.mockReset()
})

describe("PatternDocMarkdown", () => {
  describe("plain markdown", () => {
    it("renders headings and paragraphs", () => {
      render(
        <PatternDocMarkdown
          markdown={"# Feedback Loop\n\nAn agentic pattern."}
        />,
      )

      expect(
        screen.getByRole("heading", { level: 1, name: "Feedback Loop" }),
      ).toBeInTheDocument()
      expect(screen.getByText("An agentic pattern.")).toBeInTheDocument()
    })

    it("renders inline code without invoking mermaid", () => {
      render(
        <PatternDocMarkdown
          markdown={"Use the `read_pattern_doc` tool to fetch the spec."}
        />,
      )

      expect(screen.getByText("read_pattern_doc")).toBeInTheDocument()
      expect(mockRender).not.toHaveBeenCalled()
    })
  })

  describe("mermaid fenced blocks", () => {
    it("renders MermaidBlock when a ```mermaid``` fence is present", async () => {
      mockRender.mockResolvedValue({ svg: '<svg data-test="chart"/>' })

      const md = [
        "# Pattern",
        "",
        "```mermaid",
        "graph TD",
        "  A --> B",
        "```",
        "",
        "Trailing paragraph.",
      ].join("\n")

      render(<PatternDocMarkdown markdown={md} />)

      expect(screen.getByTestId("mermaid-loading")).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByTestId("mermaid-svg")).toBeInTheDocument()
      })

      const svgHost = screen.getByTestId("mermaid-svg")
      expect(svgHost.querySelector("svg")).not.toBeNull()

      expect(mockRender).toHaveBeenCalledOnce()
      const [, chartArg] = mockRender.mock.calls[0]
      expect(chartArg).toBe("graph TD\n  A --> B")

      expect(
        screen.getByRole("heading", { level: 1, name: "Pattern" }),
      ).toBeInTheDocument()
      expect(screen.getByText("Trailing paragraph.")).toBeInTheDocument()
    })

    it("falls back to raw <pre> when mermaid throws", async () => {
      mockRender.mockRejectedValue(new Error("parse error: invalid syntax"))

      const md = ["```mermaid", "not a real diagram", "```"].join("\n")

      render(<PatternDocMarkdown markdown={md} />)

      await waitFor(() => {
        expect(screen.getByTestId("mermaid-fallback")).toBeInTheDocument()
      })

      const fallback = screen.getByTestId("mermaid-fallback")
      expect(fallback.textContent).toContain("not a real diagram")
    })
  })

  describe("non-mermaid fenced code", () => {
    it("leaves other language fences alone", () => {
      const md = ["```python", "print('hi')", "```"].join("\n")

      render(<PatternDocMarkdown markdown={md} />)

      expect(screen.getByText("print('hi')")).toBeInTheDocument()
      expect(mockRender).not.toHaveBeenCalled()
    })
  })
})
