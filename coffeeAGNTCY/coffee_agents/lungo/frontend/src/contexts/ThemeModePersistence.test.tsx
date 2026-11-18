/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { act, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { OpenUiKitThemeBridge } from "@/contexts/OpenUiKitThemeBridge"
import { useAppThemeMode } from "@/hooks/useApp"
import { THEME_MODE_STORAGE_KEY } from "@/utils/themeStorage"

type SchemeListener = (event: MediaQueryListEvent) => void

function installMatchMedia(matches: boolean) {
  const listeners = new Set<SchemeListener>()
  const media = {
    matches,
    addEventListener: (_type: string, listener: SchemeListener) => {
      listeners.add(listener)
    },
    removeEventListener: (_type: string, listener: SchemeListener) => {
      listeners.delete(listener)
    },
    emit(next: boolean) {
      media.matches = next
      for (const listener of listeners) {
        listener({ matches: next } as MediaQueryListEvent)
      }
    },
    listenerCount: () => listeners.size,
  }
  vi.stubGlobal("matchMedia", () => media)
  return media
}

function ThemeProbe() {
  const { mode, setThemePreference } = useAppThemeMode()
  return (
    <>
      <div>{mode}</div>
      <button type="button" onClick={() => setThemePreference("light")}>
        Light
      </button>
      <button type="button" onClick={() => setThemePreference("system")}>
        System
      </button>
    </>
  )
}

afterEach(() => {
  localStorage.clear()
  vi.unstubAllGlobals()
})

describe("ThemeModePersistence", () => {
  it("follows the OS when nothing is saved and stops after an explicit choice", () => {
    const media = installMatchMedia(false)

    render(
      <OpenUiKitThemeBridge>
        <ThemeProbe />
      </OpenUiKitThemeBridge>,
    )

    expect(localStorage.getItem(THEME_MODE_STORAGE_KEY)).toBeNull()
    expect(screen.getByText("light")).toBeInTheDocument()
    expect(media.listenerCount()).toBe(1)

    act(() => {
      media.emit(true)
    })
    expect(screen.getByText("dark")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "Light" }))

    expect(localStorage.getItem(THEME_MODE_STORAGE_KEY)).toBe("light")
    expect(screen.getByText("light")).toBeInTheDocument()

    act(() => {
      media.emit(false)
    })
    expect(screen.getByText("light")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "System" }))

    expect(localStorage.getItem(THEME_MODE_STORAGE_KEY)).toBe("system")
    expect(screen.getByText("light")).toBeInTheDocument()

    act(() => {
      media.emit(true)
    })
    expect(screen.getByText("dark")).toBeInTheDocument()
  })
})
