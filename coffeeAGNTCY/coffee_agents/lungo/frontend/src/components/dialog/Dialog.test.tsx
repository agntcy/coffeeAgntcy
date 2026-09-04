/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { ThemeProvider } from "@open-ui-kit/core"
import { render, screen } from "@testing-library/react"
import type { ComponentProps, ReactNode } from "react"
import { describe, expect, it, vi } from "vitest"
import Dialog from "./Dialog"

const renderDialog = (
  props: Partial<ComponentProps<typeof Dialog>> & { children?: ReactNode } = {},
) =>
  render(
    <ThemeProvider>
      <Dialog open onClose={vi.fn()} title="About" {...props}>
        {props.children ?? "Body"}
      </Dialog>
    </ThemeProvider>,
  )

describe("Dialog", () => {
  it("does not render a footer divider when footer has no children", () => {
    renderDialog()
    expect(screen.queryByRole("separator")).not.toBeInTheDocument()
    expect(
      screen.queryByRole("button", { name: "Save" }),
    ).not.toBeInTheDocument()
  })

  it("does not render a footer divider for empty footer nodes", () => {
    const { rerender } = renderDialog({ footer: null })
    expect(screen.queryByRole("separator")).not.toBeInTheDocument()

    rerender(
      <ThemeProvider>
        <Dialog open onClose={vi.fn()} title="About" footer={false}>
          Body
        </Dialog>
      </ThemeProvider>,
    )
    expect(screen.queryByRole("separator")).not.toBeInTheDocument()

    rerender(
      <ThemeProvider>
        <Dialog open onClose={vi.fn()} title="About" footer={<>{null}</>}>
          Body
        </Dialog>
      </ThemeProvider>,
    )
    expect(screen.queryByRole("separator")).not.toBeInTheDocument()
  })

  it("renders a footer divider when footer has children", () => {
    renderDialog({ footer: <button type="button">Save</button> })
    expect(screen.getByRole("separator")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument()
  })
})
