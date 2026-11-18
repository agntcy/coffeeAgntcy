/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
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
  const [record, setRecord] = useState<OasfRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestIdRef = useRef(0)

  const loadRecord = useCallback(() => {
    if (!nodeData) return
    const requestId = ++requestIdRef.current
    setRecord(null)
    setError(null)
    setLoading(true)
    void fetchOasfRecord(nodeData)
      .then((nextRecord) => {
        if (requestId === requestIdRef.current) {
          setRecord(nextRecord)
        }
      })
      .catch((err: OasfApiError) => {
        if (requestId === requestIdRef.current) {
          setError(
            err.message ??
              "An unexpected error occurred while fetching OASF record.",
          )
        }
      })
      .finally(() => {
        if (requestId === requestIdRef.current) {
          setLoading(false)
        }
      })
  }, [nodeData])

  useEffect(() => {
    if (!isOpen || !nodeData) {
      requestIdRef.current += 1
      return
    }
    loadRecord()
    return () => {
      requestIdRef.current += 1
    }
  }, [isOpen, nodeData, loadRecord])

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
          actionCallback: loadRecord,
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
