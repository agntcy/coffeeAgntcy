/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import { Box, LoadingErrorState, Stack, Typography } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { LoadingSpinner } from "@/components/loading/LoadingSpinner"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphDialogLoadingOverlaySx,
  graphDialogPreSx,
  graphDialogScrollBodySx,
} from "../graphDialogStyles"
import { fetchOasfRecord, OasfRecord, OasfApiError } from "./DirectoryApi"

export interface OasfRecordModalProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData?: Record<string, unknown> | null
}

const OasfRecordModal: React.FC<OasfRecordModalProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
}) => {
  const [attempt, setAttempt] = useState(0)
  const [wasOpen, setWasOpen] = useState(isOpen)
  const [settled, setSettled] = useState<{
    nodeData: Record<string, unknown>
    attempt: number
    record: OasfRecord | null
    error: string | null
  } | null>(null)
  if (isOpen !== wasOpen) {
    setWasOpen(isOpen)
    if (isOpen) setAttempt((current) => current + 1)
  }

  useEffect(() => {
    if (!isOpen || !nodeData) return
    let cancelled = false
    const requestedNode = nodeData
    const requestedAttempt = attempt
    void fetchOasfRecord(requestedNode)
      .then((data) => {
        if (cancelled) return
        setSettled({
          nodeData: requestedNode,
          attempt: requestedAttempt,
          record: data,
          error: null,
        })
      })
      .catch((err: OasfApiError) => {
        if (cancelled) return
        setSettled({
          nodeData: requestedNode,
          attempt: requestedAttempt,
          record: null,
          error:
            err.message ??
            "An unexpected error occurred while fetching OASF record.",
        })
      })
    return () => {
      cancelled = true
    }
  }, [isOpen, nodeData, attempt])

  const isCurrent =
    isOpen &&
    Boolean(nodeData) &&
    settled !== null &&
    settled.nodeData === nodeData &&
    settled.attempt === attempt
  const loading = isOpen && Boolean(nodeData) && !isCurrent
  const record = isCurrent ? settled.record : null
  const error = isCurrent ? settled.error : null

  const retryFetch = useCallback(() => {
    setAttempt((current) => current + 1)
  }, [])

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="Directory Information"
      PaperProps={
        { "data-modal-content": "" } as React.ComponentProps<
          typeof Dialog
        >["PaperProps"]
      }
    >
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
              fontWeight={600}
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
    </Dialog>
  )
}

export default OasfRecordModal
