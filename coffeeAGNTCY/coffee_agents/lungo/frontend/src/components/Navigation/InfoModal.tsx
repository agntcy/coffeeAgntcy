/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import { fetchJson } from "@/api/http"
import { reportRequestError } from "@/errors/request"
import {
  buildAboutRequest,
  getAgenticWorkflowsApiUrl,
  getExchangeAppApiUrl,
} from "@/urls"

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

const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose }) => {
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
    <Dialog open={isOpen} onClose={onClose} aria-labelledby="info-modal-title">
      <DialogTitle id="info-modal-title">
        <IconButton
          aria-label="Close"
          onClick={onClose}
          sx={{
            position: "absolute",
            right: 8,
            top: 8,
          }}
        >
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          <Stack spacing={2}>
            <Typography variant="h6">Build and Release Information</Typography>
            <Stack spacing={1}>
              {error && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}
              <Stack direction="row" justifyContent="space-between">
                <Typography component="span" variant="body2">
                  Agentic Workflows API:
                </Typography>
                <Typography component="span" variant="body2">
                  {AGENTIC_WORKFLOWS_API_URL}
                </Typography>
              </Stack>
              <Stack direction="row" justifyContent="space-between">
                <Typography component="span" variant="body2">
                  Release Version:
                </Typography>
                <Typography component="span" variant="body2">
                  {info?.version ?? "…"}
                </Typography>
              </Stack>
              <Stack direction="row" justifyContent="space-between">
                <Typography component="span" variant="body2">
                  Build Date:
                </Typography>
                <Typography component="span" variant="body2">
                  {info?.build_date ?? "…"}
                </Typography>
              </Stack>
            </Stack>
          </Stack>

          <Stack spacing={2}>
            <Typography variant="h6">Dependencies:</Typography>
            <Stack spacing={1}>
              {info?.dependencies &&
                Object.entries(info.dependencies).map(([name, ver]) => (
                  <Stack
                    key={name}
                    direction="row"
                    justifyContent="space-between"
                  >
                    <Typography component="span" variant="body2">
                      {name}:
                    </Typography>
                    <Typography component="span" variant="body2">
                      {ver}
                    </Typography>
                  </Stack>
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
      </DialogContent>
    </Dialog>
  )
}

export default InfoModal
