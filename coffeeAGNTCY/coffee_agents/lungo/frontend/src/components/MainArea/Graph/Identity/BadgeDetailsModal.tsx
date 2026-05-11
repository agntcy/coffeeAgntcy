/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import {
  Box,
  Button,
  IconButton,
  Modal,
  ModalContent,
  ModalTitle,
  Stack,
  Typography,
} from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import { BadgeData } from "./types"
import { CustomNodeData } from "../Elements/types"
import { logger } from "@/utils/logger"
import { fetchBadgeDetails, IdentityServiceError } from "./IdentityApi"
import { LoadingSpinner } from "@/components/loading"
import {
  graphModalLoadingOverlaySx,
  graphModalPreSx,
  graphModalScrollBodySx,
} from "../graphModalStyles"

interface BadgeDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const BadgeDetailsModal: React.FC<BadgeDetailsModalProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
}) => {
  const [badgeData, setBadgeData] = useState<BadgeData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchBadgeDetailsData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchBadgeDetails(nodeData)
      setBadgeData(data)
    } catch (error) {
      const identityError = error as IdentityServiceError
      logger.error("Error fetching badge details:", identityError)
      setError(
        identityError.message ||
          "An unexpected error occurred while fetching badge details.",
      )
    } finally {
      setLoading(false)
    }
  }, [nodeData])

  useEffect(() => {
    if (isOpen && nodeData) {
      fetchBadgeDetailsData()
    }
  }, [fetchBadgeDetailsData, isOpen, nodeName, nodeData])

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <ModalTitle sx={{ pr: 6, position: "relative" }}>
        {nodeName} Badge Details
        <IconButton
          onClick={onClose}
          aria-label="Close"
          size="small"
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <Close sx={{ fontSize: 18 }} />
        </IconButton>
      </ModalTitle>

      <ModalContent dividers>
        {loading && !badgeData ? (
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
                Failed to load badge details
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
              onClick={fetchBadgeDetailsData}
            >
              Retry
            </Button>
          </Stack>
        ) : badgeData ? (
          <Stack sx={graphModalScrollBodySx}>
            <Box component="pre" sx={graphModalPreSx}>
              {JSON.stringify(badgeData, null, 2)}
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

export default BadgeDetailsModal
