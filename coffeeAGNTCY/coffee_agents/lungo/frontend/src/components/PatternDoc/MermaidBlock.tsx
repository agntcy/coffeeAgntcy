/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useId, useRef, useState } from "react"
import mermaid from "mermaid"
import { Box, Typography, useTheme } from "@open-ui-kit/core"
import { logger } from "@/utils/logger"

interface MermaidBlockProps {
  chart: string
}

/**
 * Max label widths before text wraps. Narrow labels keep the diagram narrow,
 * which matters because mermaid scales an oversized diagram (text included)
 * down to the panel width. Edge labels get more room than node labels: they
 * are short enough to stay on one line, and wrapping them reads poorly on
 * their filled chip.
 */
const NODE_LABEL_WRAP_WIDTH_PX = 110
const EDGE_LABEL_WRAP_WIDTH_PX = 160

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
            // Opaque: mermaid drops the alpha of a translucent value and
            // repaints it at 50%, which leaves labels on a mid-gray plate.
            edgeLabelBackground: palette.primary.main,
            // Subgraph frames: mermaid otherwise falls back to its own
            // near-black title and a derived border unrelated to the palette.
            titleColor: palette.text.primary,
            clusterBorder: palette.divider,
            fontFamily: theme.typography.fontFamily,
            // Sets both node and edge labels. Mermaid scales wide diagrams
            // down to the panel width, so start from the larger body size.
            fontSize: String(theme.typography.body1.fontSize),
          },
          // Edge labels sit on `edgeLabelBackground`, the node labels on
          // `primaryColor`, but mermaid colors both from `textColor`. Repaint
          // only the edge labels for the filled chip they actually sit on.
          themeCSS: `
            .edgeLabel, .edgeLabel p, .edgeLabel span {
              color: ${palette.primary.contrastText};
              fill: ${palette.primary.contrastText};
              /* The flowchart wrappingWidth below covers node labels only. */
              white-space: normal !important;
              max-width: ${EDGE_LABEL_WRAP_WIDTH_PX}px;
              overflow-wrap: break-word;
            }
            .edgeLabel p {
              padding: ${theme.spacing(0.25, 0.75)};
            }
          `,
          flowchart: {
            // Not "basis": its spline ignores the layout points, so mermaid
            // places edge labels off their reserved slots and they collide.
            curve: "natural",
            padding: 20,
            nodeSpacing: 50,
            rankSpacing: 60,
            wrappingWidth: NODE_LABEL_WRAP_WIDTH_PX,
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
      <Box
        component="pre"
        sx={{
          overflowX: "auto",
          m: 0,
          p: 1.5,
          borderRadius: 1,
          bgcolor: "action.hover",
          fontSize: (theme) => theme.typography.caption.fontSize,
        }}
        data-testid="mermaid-fallback"
      >
        <code>{chart}</code>
      </Box>
    )
  }

  if (!svg) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          p: 2,
        }}
        data-testid="mermaid-loading"
      >
        {/* Muted via opacity, matching PatternDocCanvas: the light theme maps
            `text.secondary` to a near-white gray that is unreadable on paper. */}
        <Typography variant="body2" sx={{ opacity: 0.6 }}>
          Rendering diagram…
        </Typography>
      </Box>
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
