/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { EdgeLabelRenderer } from "@xyflow/react"
import { Box } from "@open-ui-kit/core"

interface CustomEdgeLabelProps {
  x: number
  y: number
  label?: string
  active?: boolean
}

const CustomEdgeLabel: React.FC<CustomEdgeLabelProps> = ({
  x,
  y,
  label,
  active,
}) => {
  const isSlimLabel = label?.includes("SLIM")
  const isValidateLabel = label?.toLowerCase().includes("validate")
  const isMcpLabel = label?.includes("MCP")
  const isLongLabel =
    isSlimLabel || isValidateLabel || isMcpLabel || (label && label.length > 6)

  return (
    <EdgeLabelRenderer>
      <Box
        sx={{
          pointerEvents: "none",
          position: "absolute",
          left: x,
          top: y,
          zIndex: 9999,
          transform: "translate(-50%, -50%)",
          height: 20,
          px: 0.75,
          py: 0.25,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: isLongLabel ? 0.75 : 0.5,
          minWidth: isLongLabel ? 80 : 34,
          maxWidth: isLongLabel ? 120 : 34,
          borderRadius: (theme) => theme.shape.borderRadius,
          typography: "caption",
          fontWeight: 400,
          lineHeight: "16px",
          bgcolor: active ? "primary.main" : "background.paper",
          color: active ? "primary.contrastText" : "text.primary",
          boxShadow: 0,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {label ?? ""}
      </Box>
    </EdgeLabelRenderer>
  )
}

export default CustomEdgeLabel
