/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import ChatMarkdown from "./ChatMarkdown"

describe("ChatMarkdown", () => {
  it("renders bold and headings as elements", () => {
    render(<ChatMarkdown content={"# Title\n\nSome **bold** text."} />)
    expect(
      screen.getByRole("heading", { level: 1, name: "Title" }),
    ).toBeInTheDocument()
    expect(screen.getByText("bold").tagName).toBe("STRONG")
  })

  it("renders explicit links opening in a new tab", () => {
    render(<ChatMarkdown content={"[AGNTCY](https://agntcy.org)"} />)
    const link = screen.getByRole("link", { name: "AGNTCY" })
    expect(link).toHaveAttribute("href", "https://agntcy.org")
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", "noopener noreferrer")
  })

  it("autolinks bare URLs (GFM)", () => {
    render(<ChatMarkdown content={"See https://github.com/agntcy/dir"} />)
    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", "https://github.com/agntcy/dir")
  })

  it("renders bullet lists", () => {
    render(<ChatMarkdown content={"- one\n- two"} />)
    expect(screen.getAllByRole("listitem")).toHaveLength(2)
  })

  it("preserves single newlines as line breaks (remark-breaks)", () => {
    const { container } = render(
      <ChatMarkdown content={"line one\nline two"} />,
    )
    expect(container.querySelector("br")).not.toBeNull()
  })

  it("does not render embedded HTML as live elements", () => {
    const { container } = render(
      <ChatMarkdown content={"Hi <img src=x onerror=alert(1) />"} />,
    )
    // Raw HTML is escaped (no rehype-raw), so no live <img> is ever created.
    expect(container.querySelector("img")).toBeNull()
  })
})
