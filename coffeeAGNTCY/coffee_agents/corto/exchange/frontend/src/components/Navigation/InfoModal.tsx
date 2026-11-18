/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useState } from "react"
import type { SxProps, Theme } from "@mui/material/styles"
import { Stack, Typography } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { env } from "@/utils/env"

interface InfoModalProps {
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

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  env.get("VITE_EXCHANGE_APP_API_URL") ?? DEFAULT_EXCHANGE_APP_API_URL

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

const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose }) => {
  const [info, setInfo] = useState<BuildInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    let cancelled = false
    const fetchInfo = async () => {
      try {
        setError(null)
        const res = await fetch(`${EXCHANGE_APP_API_URL}/about`)
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        const data = await res.json()
        if (!cancelled) setInfo(data)
      } catch {
        if (!cancelled) setError("Failed to load build info")
      }
    }
    void fetchInfo()
    return () => {
      cancelled = true
    }
  }, [isOpen])

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
              Object.entries(info.dependencies).map(([k, v]) => (
                <InfoDialogRow key={k} label={`${k}:`} value={v} />
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

export default InfoModal
