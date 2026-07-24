/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { alpha } from "@mui/material/styles"
import type { Theme } from "@mui/material/styles"

import type { AgentTransport } from "./transportMeta"

export function normalizeTransportName(value: string | undefined): string {
  return value?.trim().toLowerCase() ?? ""
}

export function getRailThemeColors(theme: Theme) {
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
