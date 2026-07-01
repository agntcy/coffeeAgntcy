/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import type { SxProps, Theme } from "@mui/material/styles"
import grafanaIcon from "@/assets/grafana.svg"
import { buildGrafanaSessionDashboardUrl } from "@/urls"
import ExternalLinkButton from "./ExternalLinkButton"

export interface GrafanaSessionLinkProps {
  sessionId: string | null | undefined
  sx?: SxProps<Theme>
}

const GrafanaSessionLink: React.FC<GrafanaSessionLinkProps> = ({
  sessionId,
  sx,
}) => {
  if (!sessionId) return null

  return (
    <ExternalLinkButton
      component="button"
      url={buildGrafanaSessionDashboardUrl(sessionId)}
      label="Grafana"
      iconSrc={grafanaIcon}
      sx={(theme) => ({
        ml: 1,
        "& .MuiChip-label": theme.typography.body1,
        ...((typeof sx === "function" ? sx(theme) : sx) as object),
      })}
    />
  )
}

export default GrafanaSessionLink
