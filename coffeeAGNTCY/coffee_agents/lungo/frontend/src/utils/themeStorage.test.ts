/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { afterEach, describe, expect, it, vi } from "vitest"

import {
  THEME_MODE_STORAGE_KEY,
  readOsColorScheme,
  readStoredThemeMode,
  resolveStoredColorScheme,
  subscribeToOsColorScheme,
  writeStoredThemeMode,
} from "./themeStorage"

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
  }
  vi.stubGlobal("matchMedia", () => media)
  return media
}

afterEach(() => {
  localStorage.clear()
  vi.unstubAllGlobals()
})

describe("themeStorage", () => {
  it("stores light, dark, and system, and ignores any other saved value", () => {
    writeStoredThemeMode("system")

    expect(localStorage.getItem(THEME_MODE_STORAGE_KEY)).toBe("system")
    expect(readStoredThemeMode()).toBe("system")

    localStorage.setItem(THEME_MODE_STORAGE_KEY, "nope")
    localStorage.setItem("theme", "light")

    expect(readStoredThemeMode()).toBeNull()
  })

  it("reads the OS color scheme and falls back to dark without matchMedia", () => {
    installMatchMedia(true)
    expect(readOsColorScheme()).toBe("dark")

    installMatchMedia(false)
    expect(readOsColorScheme()).toBe("light")

    vi.stubGlobal("matchMedia", undefined)
    expect(readOsColorScheme()).toBe("dark")
  })

  it("treats a missing preference as the current OS scheme", () => {
    installMatchMedia(false)

    expect(resolveStoredColorScheme(null)).toBe("light")
    expect(resolveStoredColorScheme("system")).toBe("light")
    expect(resolveStoredColorScheme("dark")).toBe("dark")
  })

  it("notifies subscribers when the OS scheme changes and stops after unsubscribe", () => {
    const media = installMatchMedia(false)
    const onChange = vi.fn()
    const unsubscribe = subscribeToOsColorScheme(onChange)

    media.emit(true)
    unsubscribe()
    media.emit(false)

    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith("dark")
  })
})
