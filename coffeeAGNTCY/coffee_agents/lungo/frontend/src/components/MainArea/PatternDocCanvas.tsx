/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useMemo } from "react"
import { Box, Typography } from "@open-ui-kit/core"
import PatternDocMarkdown from "@/components/PatternDoc/PatternDocMarkdown"
import type { PatternDocState } from "@/types/patternDoc"

export interface PatternDocCanvasProps {
  selectedReferencePattern: string
  patternDocState: PatternDocState
}

const PatternDocCanvas: React.FC<PatternDocCanvasProps> = React.memo(
  ({ selectedReferencePattern, patternDocState }) => {
    const overlayMessage = useMemo<string | null>(() => {
      switch (patternDocState.status) {
        case "loading":
          return "Loading documentation…"
        case "not_found":
          return `No documentation available for "${selectedReferencePattern}" yet.`
        case "error":
          return (
            patternDocState.errorMessage ??
            "Failed to load documentation. Try again later."
          )
        default:
          return null
      }
    }, [patternDocState, selectedReferencePattern])

    const isReady =
      patternDocState.status === "ready" &&
      patternDocState.documentation !== null

    return (
      <Box
        data-testid="pattern-doc-canvas"
        sx={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {isReady && patternDocState.documentation && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              width: "100%",
              height: "100%",
              px: 2,
              py: 1.5,
              overflow: "hidden",
            }}
          >
            <Box
              data-testid="pattern-doc-node"
              sx={{
                display: "flex",
                flexDirection: "column",
                width: "100%",
                height: "100%",
                overflow: "hidden",
                borderRadius: 2,
                border: 1,
                borderColor: "divider",
                bgcolor: "background.paper",
              }}
            >
              <Box
                component="header"
                sx={{
                  flexShrink: 0,
                  borderBottom: 1,
                  borderColor: "divider",
                  px: 3,
                  py: 2,
                }}
              >
                <Typography variant="h6">
                  {patternDocState.documentation.title}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{ mt: 0.5, display: "block", opacity: 0.6 }}
                >
                  Reference Library
                </Typography>
              </Box>
              <Box
                data-testid="pattern-doc-body"
                sx={{
                  flex: 1,
                  minHeight: 0,
                  overflowY: "auto",
                  px: 3,
                  py: 2,
                }}
              >
                <PatternDocMarkdown
                  markdown={patternDocState.documentation.full_markdown}
                />
              </Box>
            </Box>
          </Box>
        )}
        {overlayMessage !== null && (
          <Box
            role={patternDocState.status === "error" ? "alert" : "status"}
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              height: "100%",
              px: 3,
              textAlign: "center",
            }}
          >
            <Typography variant="body2" sx={{ opacity: 0.6 }}>
              {overlayMessage}
            </Typography>
          </Box>
        )}
      </Box>
    )
  },
)
PatternDocCanvas.displayName = "PatternDocCanvas"

export default PatternDocCanvas
