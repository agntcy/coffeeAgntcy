/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import type { SxProps, Theme } from "@mui/material/styles"
import { Stack, Typography } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { fetchJson } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import {
  buildAboutRequest,
  getAgenticWorkflowsApiUrl,
  getExchangeAppApiUrl,
} from "@/urls"

interface InfoDialogProps {
  isOpen: boolean
  onClose: () => void
}

interface BuildInfo {
  app: string
  service: string
  version: string
  build_date: string
  build_timestamp: string
  image: string
  dependencies: Record<string, string>
}

const infoDialogRowSx: SxProps<Theme> = {
  flexDirection: "row",
  flexWrap: "wrap",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 1,
  minWidth: 0,
}

const infoDialogLabelSx: SxProps<Theme> = {
  flexShrink: 0,
}

const infoDialogValueSx: SxProps<Theme> = {
  wordBreak: "break-word",
  overflowWrap: "anywhere",
  textAlign: { xs: "left", sm: "right" },
  minWidth: 0,
  flex: { sm: "1 1 12rem" },
}

function InfoDialogRow({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <Stack sx={infoDialogRowSx}>
      <Typography component="span" variant="body2" sx={infoDialogLabelSx}>
        {label}
      </Typography>
      <Typography component="span" variant="body2" sx={infoDialogValueSx}>
        {value}
      </Typography>
    </Stack>
  )
}

const InfoDialog: React.FC<InfoDialogProps> = ({ isOpen, onClose }) => {
  const EXCHANGE_APP_API_URL = getExchangeAppApiUrl()
  const AGENTIC_WORKFLOWS_API_URL = getAgenticWorkflowsApiUrl()

  const [info, setInfo] = React.useState<BuildInfo | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    let cancelled = false
    const fetchInfo = async () => {
      const request = buildAboutRequest()
      try {
        setError(null)
        const data = await fetchJson<BuildInfo>(request.url, {
          endpointLabel: request.endpointLabel,
        })
        if (!cancelled) setInfo(data)
      } catch (err) {
        if (!cancelled) {
          const httpError = reportRequestError(request.endpointLabel, err)
          setError(httpError.message)
          setInfo(null)
        }
      }
    }
    fetchInfo()
    return () => {
      cancelled = true
    }
  }, [isOpen, EXCHANGE_APP_API_URL])

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="sm"
      title="About"
      titleProps={{ id: "info-dialog-title" }}
      aria-labelledby="info-dialog-title"
    >
      <Stack spacing={3}>
        <Stack spacing={2}>
          <Typography variant="h6">Build and Release Information</Typography>
          <Stack spacing={1}>
            {error && (
              <Typography variant="body2" color="error">
                {error}
              </Typography>
            )}
            <InfoDialogRow
              label="Agentic Workflows API:"
              value={AGENTIC_WORKFLOWS_API_URL}
            />
            <InfoDialogRow
              label="Release Version:"
              value={info?.version ?? "…"}
            />
            <InfoDialogRow
              label="Build Date:"
              value={info?.build_date ?? "…"}
            />
          </Stack>
        </Stack>

        <Stack spacing={2}>
          <Typography variant="h6">Dependencies:</Typography>
          <Stack spacing={1}>
            {info?.dependencies &&
              Object.entries(info.dependencies).map(([name, ver]) => (
                <InfoDialogRow key={name} label={`${name}:`} value={ver} />
              ))}
            {!info?.dependencies && !error && (
              <Typography variant="body2">Loading...</Typography>
            )}
            {!info?.dependencies && error && (
              <Typography color="error" variant="body2">
                No dependency info
              </Typography>
            )}
          </Stack>
        </Stack>
      </Stack>
    </Dialog>
  )
}

export default InfoDialog
