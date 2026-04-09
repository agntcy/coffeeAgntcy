/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import { X } from "lucide-react"
import DialogTitle from "@mui/material/DialogTitle"
import {
  Dialog,
  IconButton,
  ModalContent,
  Stack,
  Typography,
} from "@open-ui-kit/core"
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

const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose }) => {
  const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
  const EXCHANGE_APP_API_URL =
    env.get("VITE_EXCHANGE_APP_API_URL") || DEFAULT_EXCHANGE_APP_API_URL

  const [info, setInfo] = React.useState<BuildInfo | null>(null)
  const [error, setError] = React.useState<string | null>(null)

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
        if (!cancelled) {
          setError("Failed to load build info")
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
        Build and Release Information
        <IconButton
          aria-label="Close"
          onClick={onClose}
          size="small"
          sx={{
            position: "absolute",
            right: 8,
            top: 8,
          }}
        >
          <X />
        </IconButton>
      </DialogTitle>

      <ModalContent>
        <Stack spacing={3}>
          <Stack spacing={2}>
            <Stack spacing={1}>
              {error && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}
              <Stack
                direction="row"
                justifyContent="space-between"
                sx={{
                  typography: "body2",
                }}
              >
                <Typography component="span" variant="body2">
                  Release Version:
                </Typography>
                <Typography
                  component="span"
                  variant="body2"
                  color="var(--modal-accent)"
                >
                  {info?.version ?? "…"}
                </Typography>
              </Stack>
              <Stack
                direction="row"
                justifyContent="space-between"
                sx={{
                  typography: "body2",
                }}
              >
                <Typography component="span" variant="body2" color="inherit">
                  Build Date:
                </Typography>
                <Typography
                  component="span"
                  variant="body2"
                  color="var(--modal-accent)"
                >
                  {info?.build_date ?? "…"}
                </Typography>
              </Stack>
            </Stack>
          </Stack>

          <Stack spacing={2}>
            <Typography
              variant="h6"
              sx={{
                color: "var(--modal-text)",
              }}
            >
              Dependencies:
            </Typography>
            <Stack spacing={1}>
              {info?.dependencies &&
                Object.entries(info.dependencies).map(([name, ver]) => (
                  <Stack
                    key={name}
                    direction="row"
                    justifyContent="space-between"
                    sx={{
                      typography: "body2",
                    }}
                  >
                    <Typography component="span" variant="body2">
                      {name}:
                    </Typography>
                    <Typography
                      component="span"
                      variant="body2"
                      sx={{
                        color: "var(--modal-accent)",
                      }}
                    >
                      {ver}
                    </Typography>
                  </Stack>
                ))}
              {!info?.dependencies && !error && (
                <Typography variant="body2" color="var(--modal-text-secondary)">
                  Loading…
                </Typography>
              )}
              {!info?.dependencies && error && (
                <Typography variant="body2" color="var(--modal-text-secondary)">
                  No dependency info
                </Typography>
              )}
            </Stack>
          </Stack>
        </Stack>
      </ModalContent>
    </Dialog>
  )
}

export default InfoModal
