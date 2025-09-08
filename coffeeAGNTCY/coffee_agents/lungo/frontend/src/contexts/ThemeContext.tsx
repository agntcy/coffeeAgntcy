/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, ReactNode } from "react"
import { ThemeContext, Theme, ThemeContextType } from "./theme"

interface ThemeProviderProps {
  children: ReactNode
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem("theme")
    return (savedTheme as Theme) || "dark"
  })

  const [systemTheme, setSystemTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined" && window.matchMedia) {
      return window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark"
    }
    return "dark"
  })

  const resolvedTheme: "light" | "dark" =
    theme === "system" ? systemTheme : (theme as "light" | "dark")

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: light)")
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? "light" : "dark")
    }

    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [])

  useEffect(() => {
    document.body.classList.add("theme-switching")

    if (resolvedTheme === "light") {
      document.body.setAttribute("data-theme", "light")
    } else {
      document.body.removeAttribute("data-theme")
    }

    localStorage.setItem("theme", theme)

    const timeoutId = setTimeout(() => {
      document.body.classList.remove("theme-switching")
    }, 100)

    return () => {
      clearTimeout(timeoutId)
    }
  }, [theme, resolvedTheme])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  const toggleTheme = () => {
    if (resolvedTheme === "light") {
      setThemeState("dark")
    } else {
      setThemeState("light")
    }
  }

  const isLightMode = resolvedTheme === "light"

  const value: ThemeContextType = {
    theme,
    setTheme,
    toggleTheme,
    isLightMode,
    resolvedTheme,
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
