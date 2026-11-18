/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { OpenUiKitThemeBridge } from "@/contexts/OpenUiKitThemeBridge"
import ThemeMenu from "@/components/Navigation/ThemeMenu"
import { THEME_MODE_STORAGE_KEY } from "@/utils/themeStorage"

afterEach(() => {
  localStorage.clear()
  vi.unstubAllGlobals()
})

describe("ThemeMenu", () => {
  it("saves system and keeps following the OS color scheme", () => {
    vi.stubGlobal("matchMedia", () => ({
      matches: false,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    localStorage.setItem(THEME_MODE_STORAGE_KEY, "dark")

    render(
      <OpenUiKitThemeBridge>
        <ThemeMenu />
      </OpenUiKitThemeBridge>,
    )

    fireEvent.click(screen.getByRole("button", { name: "Choose theme" }))
    fireEvent.click(screen.getByRole("menuitemradio", { name: "System" }))

    expect(localStorage.getItem(THEME_MODE_STORAGE_KEY)).toBe("system")
    expect(
      screen.getByRole("button", { name: "Choose theme" }),
    ).toBeInTheDocument()
  })
})
