/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { alpha } from "@mui/material/styles"
import type { Theme } from "@mui/material/styles"
import { Box, Typography, useTheme } from "@open-ui-kit/core"
import { transportMetaFor, type AgentTransport } from "./transportMeta"

function normalizeTransportName(value: string | undefined): string {
  return value?.trim().toLowerCase() ?? ""
}

function getRailThemeColors(theme: Theme) {
  const highlight = theme.palette.primary.main
  const highlightedText = theme.palette.primary.contrastText
  const resting =
    theme.palette.mode === "dark"
      ? theme.palette.background.paper
      : theme.palette.common.white
  const restingText = theme.palette.text.primary
  const separator = alpha(
    theme.palette.primary.main,
    theme.palette.mode === "dark" ? 0.7 : 0.55,
  )

  return { highlight, highlightedText, resting, restingText, separator }
}

export function railBackgroundImage(
  transports: AgentTransport[] | undefined,
  activeTransport: string | undefined,
  theme: Theme,
): string | undefined {
  if (!transports || transports.length === 0) return undefined

  const normalizedActive = normalizeTransportName(activeTransport)
  const railColors = getRailThemeColors(theme)
  const stops: string[] = []

  transports.forEach((transport, index) => {
    const normalizedName = normalizeTransportName(transport.name)
    const isActive =
      normalizedActive.length > 0 && normalizedName === normalizedActive
    const isPreferred = normalizedActive.length === 0 && transport.preferred
    const color =
      isActive || isPreferred ? railColors.highlight : railColors.resting
    const start = (index / transports.length) * 100
    const end = ((index + 1) / transports.length) * 100
    stops.push(`${color} ${start}%`, `${color} ${end}%`)
  })

  return `linear-gradient(to bottom, ${stops.join(", ")})`
}

const TransportRail: React.FC<{
  transports: AgentTransport[]
  expanded: boolean
  activeTransport?: string
}> = ({ transports, expanded, activeTransport }) => {
  const theme = useTheme()
  const normalizedActive = normalizeTransportName(activeTransport)
  const railColors = getRailThemeColors(theme)

  if (transports.length === 0) return null

  return (
    <Box
      aria-label="Available A2A transports"
      sx={{
        position: "absolute",
        left: 0,
        top: 0,
        bottom: 0,
        width: 8,
        display: "flex",
        flexDirection: "column",
        overflow: "visible",
        zIndex: 1,
        pointerEvents: "none",
      }}
    >
      {transports.map((transport, index) => {
        const meta = transportMetaFor(transport.name)
        const normalizedName = normalizeTransportName(transport.name)
        const isActive =
          normalizedActive.length > 0 && normalizedName === normalizedActive
        const isPreferred = normalizedActive.length === 0 && transport.preferred
        const isHighlighted = isActive || isPreferred
        const isLast = index === transports.length - 1
        const badgeText = isActive ? "active" : isPreferred ? "preferred" : null

        return (
          <Box
            key={`${transport.name}-${transport.url ?? index}`}
            sx={{
              position: "relative",
              flex: `1 1 ${100 / transports.length}%`,
              bgcolor: "transparent",
              borderBottom: isLast ? "none" : "1px solid",
              borderBottomColor: railColors.separator,
            }}
          >
            <Box
              sx={{
                position: "absolute",
                right: "100%",
                top: 0,
                height: "100%",
                display: "flex",
                alignItems: "center",
                pr: 0.75,
                opacity: expanded ? 1 : 0,
                transform: expanded ? "translateX(0)" : "translateX(8px)",
                transition: theme.transitions.create(["opacity", "transform"], {
                  duration: theme.transitions.duration.shortest,
                }),
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  minHeight: 22,
                  px: 1,
                  py: 0.25,
                  whiteSpace: "nowrap",
                  bgcolor: isHighlighted
                    ? railColors.highlight
                    : railColors.resting,
                  color: isHighlighted
                    ? railColors.highlightedText
                    : railColors.restingText,
                  border: "1px solid",
                  borderColor: isHighlighted
                    ? railColors.highlight
                    : railColors.separator,
                  borderRight: 0,
                  borderTopLeftRadius: 4,
                  borderBottomLeftRadius: 4,
                  boxShadow: theme.shadows[1],
                }}
              >
                <Typography
                  component="span"
                  sx={{
                    fontSize: 10,
                    lineHeight: "14px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                  }}
                >
                  {meta.short}
                </Typography>
                <Typography
                  component="span"
                  sx={{
                    fontSize: 9,
                    lineHeight: "13px",
                    fontWeight: 500,
                    opacity: isHighlighted ? 0.82 : 0.72,
                  }}
                >
                  {meta.label}
                </Typography>
                {badgeText && (
                  <Typography
                    component="span"
                    sx={{
                      px: 0.5,
                      py: 0.125,
                      borderRadius: 0.5,
                      bgcolor: alpha(railColors.highlightedText, 0.22),
                      color: railColors.highlightedText,
                      fontSize: 8,
                      lineHeight: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                    }}
                  >
                    {badgeText}
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>
        )
      })}
    </Box>
  )
}

export default TransportRail
