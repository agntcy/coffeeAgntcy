/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useMemo } from "react"
import {
  Box,
  Button,
  IconButton,
  Link,
  Modal,
  ModalContent,
  ModalTitle,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import { getDirectoryServerUrl, getDirectoryVersion } from "@/urls"
import { fetchOasfRecord, OasfRecord } from "./DirectoryApi"
import { CustomNodeData } from "../Elements/types"
import { IdentityServiceError } from "../Identity/IdentityApi"
import { LoadingSpinner } from "@/components/loading"
import type { ChatApiTarget } from "@/utils/patternUtils"
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
      [nodeData?.label1, nodeData?.label2]
        .filter(Boolean)
        .join(" ")
        .toLowerCase(),
    [nodeData?.label1, nodeData?.label2],
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
    } catch (err) {
      const apiError = err as IdentityServiceError
      setError(
        apiError.message ||
          "An unexpected error occurred while fetching OASF record.",
      )
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
    <Modal
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <ModalTitle sx={{ pr: 6, position: "relative" }}>
        Directory Information
        <IconButton
          onClick={onClose}
          aria-label="Close"
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <Close />
        </IconButton>
      </ModalTitle>

      <ModalContent dividers>
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
        ) : loading && !record ? (
          <Stack
            sx={{
              width: "100%",
              alignItems: "center",
              justifyContent: "center",
              py: 4,
            }}
          >
            <LoadingSpinner compact />
          </Stack>
        ) : error ? (
          <Stack
            sx={{
              width: "100%",
              alignItems: "center",
              justifyContent: "center",
              gap: 2,
              py: 4,
            }}
          >
            <Box sx={{ textAlign: "center" }}>
              <Typography variant="body1" fontWeight="medium">
                Failed to load OASF record
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 1, opacity: 0.9 }}
              >
                {error}
              </Typography>
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={fetchOasfRecordData}
            >
              Retry
            </Button>
          </Stack>
        ) : record ? (
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
            {loading && (
              <Box sx={graphModalLoadingOverlaySx}>
                <LoadingSpinner compact />
              </Box>
            )}
          </Stack>
        ) : (
          <Stack
            sx={{
              width: "100%",
              alignItems: "center",
              justifyContent: "center",
              py: 4,
            }}
          >
            <Typography color="text.primary">No data available</Typography>
          </Stack>
        )}
      </ModalContent>
    </Modal>
  )
}

export default OasfRecordModal
