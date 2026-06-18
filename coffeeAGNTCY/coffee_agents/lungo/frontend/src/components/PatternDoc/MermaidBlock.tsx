/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useId, useRef, useState } from "react"
import mermaid from "mermaid"
import { useThemeMode } from "@open-ui-kit/core"
import { logger } from "@/utils/logger"

const DARK_THEME_VARS = {
  darkMode: true,
  background: "transparent",
  primaryColor: "#1e3a5f",
  primaryTextColor: "#e8e9ea",
  primaryBorderColor: "#58c0d0",
  secondaryColor: "#2d4a6e",
  tertiaryColor: "#3a5a7e",
  lineColor: "#7670d5",
  textColor: "#e8e9ea",
  fontSize: "16px",
}

const LIGHT_THEME_VARS = {
  darkMode: false,
  background: "transparent",
  primaryColor: "#d0e8f2",
  primaryTextColor: "#1a1a1a",
  primaryBorderColor: "#3a8fb7",
  secondaryColor: "#e3eef5",
  tertiaryColor: "#f0f5fa",
  lineColor: "#5b5bbd",
  textColor: "#1a1a1a",
  fontSize: "16px",
}

interface MermaidBlockProps {
  chart: string
}

const MermaidBlock: React.FC<MermaidBlockProps> = ({ chart }) => {
  const rawId = useId()
  const svgId = `mermaid-${rawId.replace(/[^a-zA-Z0-9_-]/g, "-")}`
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<boolean>(false)
  const cancelledRef = useRef<boolean>(false)
  const { isDarkMode } = useThemeMode()

  useEffect(() => {
    cancelledRef.current = false
    setError(false)
    setSvg(null)

    const render = async (): Promise<void> => {
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: isDarkMode ? "dark" : "default",
          securityLevel: "strict",
          themeVariables: isDarkMode ? DARK_THEME_VARS : LIGHT_THEME_VARS,
          flowchart: {
            curve: "basis",
            padding: 20,
            nodeSpacing: 50,
            rankSpacing: 60,
          },
        })
        const result = await mermaid.render(svgId, chart)
        if (cancelledRef.current) return
        setSvg(result.svg)
      } catch (err) {
        if (cancelledRef.current) return
        logger.error("MermaidBlock.render", { detail: err })
        setError(true)
      }
    }

    render()

    return () => {
      cancelledRef.current = true
    }
  }, [chart, svgId, isDarkMode])

  if (error) {
    return (
      <pre
        style={{
          overflowX: "auto",
          borderRadius: 4,
          padding: 12,
          fontSize: "0.75rem",
        }}
        data-testid="mermaid-fallback"
      >
        <code>{chart}</code>
      </pre>
    )
  }

  if (!svg) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 16,
          fontSize: "0.875rem",
          opacity: 0.6,
        }}
        data-testid="mermaid-loading"
      >
        Rendering diagram…
      </div>
    )
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        overflowX: "auto",
      }}
      data-testid="mermaid-svg"
      // eslint-disable-next-line no-restricted-syntax -- mermaid.render emits SVG markup that must be mounted as HTML; the input is a trusted markdown file shipped from our own backend and the renderer is run client-side with mermaid's `securityLevel: "strict"` (no script execution, no foreign HTML).
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

export default MermaidBlock
