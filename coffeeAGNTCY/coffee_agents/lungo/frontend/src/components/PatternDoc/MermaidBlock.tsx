/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useId, useRef, useState } from "react"
import mermaid from "mermaid"
import { useTheme } from "@open-ui-kit/core"
import { logger } from "@/utils/logger"

interface MermaidBlockProps {
  chart: string
}

const MermaidBlock: React.FC<MermaidBlockProps> = ({ chart }) => {
  const rawId = useId()
  const svgId = `mermaid-${rawId.replace(/[^a-zA-Z0-9_-]/g, "-")}`
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<boolean>(false)
  const cancelledRef = useRef<boolean>(false)
  const theme = useTheme()

  useEffect(() => {
    cancelledRef.current = false
    setError(false)
    setSvg(null)

    const { palette } = theme
    const render = async (): Promise<void> => {
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: "base",
          securityLevel: "strict",
          themeVariables: {
            darkMode: palette.mode === "dark",
            background: "transparent",
            primaryColor: palette.action.hover,
            primaryBorderColor: palette.primary.main,
            primaryTextColor: palette.text.primary,
            secondaryColor: palette.action.selected,
            tertiaryColor: palette.background.default,
            lineColor: palette.primary.main,
            textColor: palette.text.primary,
            fontSize: "16px",
          },
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
  }, [chart, svgId, theme])

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
