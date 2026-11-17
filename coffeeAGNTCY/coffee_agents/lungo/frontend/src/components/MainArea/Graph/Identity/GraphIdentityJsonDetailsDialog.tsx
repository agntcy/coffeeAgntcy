/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared fetch / loading / error / JSON body for identity graph detail dialogs.
 */

import React, { useState, useEffect, useCallback } from "react"
import { Box, LoadingErrorState, Stack } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { CustomNodeData } from "../Elements/nodes/types"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphDialogLoadingOverlaySx,
  graphDialogPreSx,
  graphDialogScrollBodySx,
} from "../graphDialogStyles"

export interface GraphIdentityJsonDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
  /** Appended to node name for the dialog title, e.g. "Badge Details". */
  titleSuffix: string
  loadErrorTitle: string
  fetchData: (nodeData: CustomNodeData) => Promise<unknown>
  endpointLabelForReport: (nodeData: CustomNodeData) => string
}

const GraphIdentityJsonDetailsDialog: React.FC<
  GraphIdentityJsonDetailsDialogProps
> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
  titleSuffix,
  loadErrorTitle,
  fetchData,
  endpointLabelForReport,
}) => {
  const [attempt, setAttempt] = useState(0)
  const [settled, setSettled] = useState<{
    nodeData: CustomNodeData
    nodeName: string
    attempt: number
    data: unknown | null
    error: string | null
  } | null>(null)

  const shouldFetch = isOpen && Boolean(nodeData)

  useEffect(() => {
    if (!shouldFetch || !nodeData) return
    let cancelled = false
    const requestedNode = nodeData
    const requestedName = nodeName
    const requestedAttempt = attempt
    fetchData(requestedNode)
      .then((result) => {
        if (cancelled) return
        setSettled({
          nodeData: requestedNode,
          nodeName: requestedName,
          attempt: requestedAttempt,
          data: result,
          error: null,
        })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const httpError = reportRequestError(
          endpointLabelForReport(requestedNode),
          err,
        )
        setSettled({
          nodeData: requestedNode,
          nodeName: requestedName,
          attempt: requestedAttempt,
          data: null,
          error: httpError.message,
        })
      })
    return () => {
      cancelled = true
    }
  }, [
    shouldFetch,
    nodeData,
    nodeName,
    attempt,
    fetchData,
    endpointLabelForReport,
  ])

  const isCurrent =
    shouldFetch &&
    settled !== null &&
    settled.nodeData === nodeData &&
    settled.nodeName === nodeName &&
    settled.attempt === attempt
  const loading = shouldFetch && !isCurrent
  const data = isCurrent ? settled.data : null
  const error = isCurrent ? settled.error : null

  const retryFetch = useCallback(() => {
    setAttempt((current) => current + 1)
  }, [])

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title={`${nodeName} ${titleSuffix}`}
    >
      <LoadingErrorState
        loading={loading && data === null}
        error={error !== null}
        data={error ? null : data}
        skipEmptyCheck
        errorStateProps={{
          variant: "negative",
          ...compactNegativeEmptyStateProps,
          title: loadErrorTitle,
          description: error ?? "",
          actionTitle: "Retry",
          actionCallback: retryFetch,
        }}
        emptyStateProps={{
          variant: "info",
          title: "No data available",
        }}
      >
        {data !== null ? (
          <Stack sx={graphDialogScrollBodySx}>
            <Box component="pre" sx={graphDialogPreSx}>
              {JSON.stringify(data, null, 2)}
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

export default GraphIdentityJsonDetailsDialog
