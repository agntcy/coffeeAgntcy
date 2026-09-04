/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared fetch / loading / error / JSON body for identity graph detail dialogs.
 */

import React, { useState, useEffect, useCallback } from "react"
import { Box, LoadingErrorState, Stack } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { CustomNodeData } from "../Elements/types"
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
  const [data, setData] = useState<unknown | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchData(nodeData)
      setData(result)
    } catch (err) {
      const httpError = reportRequestError(
        endpointLabelForReport(nodeData),
        err,
      )
      setError(httpError.message)
    } finally {
      setLoading(false)
    }
  }, [endpointLabelForReport, fetchData, nodeData])

  useEffect(() => {
    if (isOpen && nodeData) {
      void loadData()
    }
  }, [isOpen, loadData, nodeData, nodeName])

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
          actionCallback: () => {
            void loadData()
          },
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
