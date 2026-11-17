/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useMemo, useCallback } from "react"
import {
  Box,
  Link,
  LoadingErrorState,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { getDirectoryServerUrl, getDirectoryVersion } from "@/urls"
import type { ChatApiTarget } from "@/utils/patternUtils"
import { fetchOasfRecord, oasfRecordRequest, OasfRecord } from "./DirectoryApi"
import { CustomNodeData } from "../Elements/nodes/types"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphDialogFieldCardSx,
  graphDialogLoadingOverlaySx,
  graphDialogPreSx,
  graphDialogScrollBodySx,
} from "../graphDialogStyles"

export interface OasfRecordDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  /** When null/undefined the dialog skips fetch (see useEffect). */
  nodeData?: CustomNodeData | null
  chatApiTarget?: ChatApiTarget | null
}

const OasfRecordDialog: React.FC<OasfRecordDialogProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
  chatApiTarget = null,
}) => {
  const directoryServerUrl = getDirectoryServerUrl()
  const directoryVersion = getDirectoryVersion()
  const [attempt, setAttempt] = useState(0)
  const [settled, setSettled] = useState<{
    nodeData: CustomNodeData
    chatApiTarget: ChatApiTarget | null
    attempt: number
    record: OasfRecord | null
    error: string | null
  } | null>(null)

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

  const shouldFetch = Boolean(isOpen && nodeData && !isDirectoryNode)

  useEffect(() => {
    if (!shouldFetch || !nodeData) return
    let cancelled = false
    const requestedNode = nodeData
    const requestedTarget = chatApiTarget
    const requestedAttempt = attempt
    fetchOasfRecord(requestedNode, requestedTarget)
      .then((data) => {
        if (cancelled) return
        setSettled({
          nodeData: requestedNode,
          chatApiTarget: requestedTarget,
          attempt: requestedAttempt,
          record: data,
          error: null,
        })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const httpError = reportRequestError(
          oasfRecordRequest(requestedNode, requestedTarget).endpointLabel,
          err,
        )
        setSettled({
          nodeData: requestedNode,
          chatApiTarget: requestedTarget,
          attempt: requestedAttempt,
          record: null,
          error: httpError.message,
        })
      })
    return () => {
      cancelled = true
    }
  }, [shouldFetch, nodeData, chatApiTarget, attempt])

  const isCurrent =
    shouldFetch &&
    settled !== null &&
    settled.nodeData === nodeData &&
    settled.chatApiTarget === chatApiTarget &&
    settled.attempt === attempt
  const loading = shouldFetch && !isCurrent
  const record = isCurrent ? settled.record : null
  const error = isCurrent ? settled.error : null

  const retryFetch = useCallback(() => {
    setAttempt((current) => current + 1)
  }, [])

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
    <Dialog open={isOpen} onClose={onClose} title="Directory Information">
      {isDirectoryNode ? (
        <Stack sx={{ width: "100%", gap: 1.5 }}>
          <Box sx={graphDialogFieldCardSx}>
            <Stack spacing={1}>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="flex-start"
                gap={2}
              >
                <Typography component="span" variant="body2">
                  Directory URL:
                </Typography>
                {directoryUrl ? (
                  <Link
                    href={directoryServerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      typography: "body2",
                      wordBreak: "break-all",
                      textAlign: "right",
                    }}
                  >
                    {directoryServerUrl}
                  </Link>
                ) : (
                  <Typography component="span" variant="body2">
                    Unavailable
                  </Typography>
                )}
              </Stack>
            </Stack>
          </Box>

          <Box sx={graphDialogFieldCardSx}>
            <Stack spacing={1}>
              <Stack direction="row" justifyContent="space-between">
                <Typography component="span" variant="body2">
                  Directory Version:
                </Typography>
                <Typography component="span" variant="body2">
                  {directoryVersion || "Unavailable"}
                </Typography>
              </Stack>
            </Stack>
          </Box>
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
            actionCallback: retryFetch,
          }}
          emptyStateProps={{
            variant: "info",
            title: "No data available",
          }}
        >
          {record ? (
            <Stack sx={graphDialogScrollBodySx}>
              <Typography
                variant="subtitle1"
                component="h3"
                fontWeight="semibold"
                sx={{ mb: 1.5 }}
              >
                {nodeName} OASF Record
              </Typography>
              <Box component="pre" sx={graphDialogPreSx}>
                {JSON.stringify(record, null, 2)}
              </Box>
              {loading ? (
                <Box sx={graphDialogLoadingOverlaySx}>
                  <LoadingSpinner compact />
                </Box>
              ) : null}
            </Stack>
          ) : null}
        </LoadingErrorState>
      )}
    </Dialog>
  )
}

export default OasfRecordDialog
