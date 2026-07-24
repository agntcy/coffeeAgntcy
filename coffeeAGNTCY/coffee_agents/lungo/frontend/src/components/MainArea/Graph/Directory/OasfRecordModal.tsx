/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useMemo } from "react"
import {
  Box,
  IconButton,
  Link,
  Dialog,
  DialogContent,
  DialogTitle,
  LoadingErrorState,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import { getDirectoryServerUrl, getDirectoryVersion } from "@/urls"
import type { ChatApiTarget } from "@/utils/patternUtils"
import { fetchOasfRecord, oasfRecordRequest, OasfRecord } from "./DirectoryApi"
import { CustomNodeData } from "../Elements/types"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { modalDialogContentSx } from "@/components/modalDialogContentSx"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphModalFieldCardSx,
  graphModalLoadingOverlaySx,
  graphModalPreSx,
  graphModalScrollBodySx,
} from "../graphModalStyles"

export interface OasfRecordModalProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  /** When null/undefined the modal skips fetch (see useEffect). */
  nodeData?: CustomNodeData | null
  chatApiTarget?: ChatApiTarget | null
}

const OasfRecordModal: React.FC<OasfRecordModalProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
  chatApiTarget = null,
}) => {
  const directoryServerUrl = getDirectoryServerUrl()
  const directoryVersion = getDirectoryVersion()
  const [record, setRecord] = useState<OasfRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const combinedLabel = useMemo(
    () =>
      [nodeData?.label, nodeData?.label_subtitle]
        .filter(Boolean)
        .join(" ")
        .toLowerCase(),
    [nodeData?.label, nodeData?.label_subtitle],
  )

  const isDirectoryNode = useMemo(
    () =>
      nodeName === "Directory" ||
      (combinedLabel.includes("agntcy") &&
        combinedLabel.includes("agent directory")),
    [nodeName, combinedLabel],
  )

  useEffect(() => {
    if (!isOpen || !nodeData) return
    if (isDirectoryNode) return // do not fetch JSON for Directory view
    fetchOasfRecordData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, nodeName, nodeData, isDirectoryNode])

  const fetchOasfRecordData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchOasfRecord(nodeData, chatApiTarget)
      setRecord(data)
    } catch (error) {
      const httpError = reportRequestError(
        oasfRecordRequest(nodeData, chatApiTarget).endpointLabel,
        error,
      )
      setError(httpError.message)
    } finally {
      setLoading(false)
    }
  }

  const nodeDataExt = nodeData as Record<string, unknown> | null | undefined
  const recordObj = record as Record<string, unknown> | null
  const directoryUrl = String(
    nodeData?.agentDirectoryLink ??
      nodeDataExt?.directoryUrl ??
      recordObj?.directory_url ??
      recordObj?.directoryUrl ??
      recordObj?.url ??
      "",
  )

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle sx={{ pr: 6, position: "relative" }}>
        Directory Information
        <IconButton
          onClick={onClose}
          aria-label="Close"
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <Close />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={modalDialogContentSx}>
        {isDirectoryNode ? (
          <Stack sx={{ width: "100%", gap: 1.5 }}>
            <Stack sx={{ width: "100%", gap: 1.5 }}>
              <Box sx={graphModalFieldCardSx}>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    opacity: 0.9,
                  }}
                >
                  Directory URL
                </Typography>
                {directoryUrl ? (
                  <Link
                    href={directoryServerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      mt: 1,
                      display: "block",
                      wordBreak: "break-all",
                      typography: "body2",
                    }}
                  >
                    {directoryServerUrl}
                  </Link>
                ) : (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 1, opacity: 0.9 }}
                  >
                    Unavailable
                  </Typography>
                )}
              </Box>

              <Box sx={graphModalFieldCardSx}>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    opacity: 0.9,
                  }}
                >
                  Directory Version
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {directoryVersion || "Unavailable"}
                </Typography>
              </Box>
            </Stack>
          </Stack>
        ) : (
          <LoadingErrorState
            loading={loading && !record}
            error={error !== null}
            data={error ? null : record}
            skipEmptyCheck
            errorStateProps={{
              variant: "negative",
              ...compactNegativeEmptyStateProps,
              title: "Failed to load OASF record",
              description: error ?? "",
              actionTitle: "Retry",
              actionCallback: () => {
                void fetchOasfRecordData()
              },
            }}
            emptyStateProps={{
              variant: "info",
              title: "No data available",
            }}
          >
            {record ? (
              <Stack sx={graphModalScrollBodySx}>
                <Typography
                  variant="subtitle1"
                  component="h3"
                  fontWeight="semibold"
                  sx={{ mb: 1.5 }}
                >
                  {nodeName} OASF Record
                </Typography>
                <Box component="pre" sx={graphModalPreSx}>
                  {JSON.stringify(record, null, 2)}
                </Box>
                {loading ? (
                  <Box sx={graphModalLoadingOverlaySx}>
                    <LoadingSpinner compact />
                  </Box>
                ) : null}
              </Stack>
            ) : null}
          </LoadingErrorState>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default OasfRecordModal
