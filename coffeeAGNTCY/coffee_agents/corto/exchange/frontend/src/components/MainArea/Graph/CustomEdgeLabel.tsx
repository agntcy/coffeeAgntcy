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
          minHeight: 20,
          px: 0.75,
          py: 0.25,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 0.75,
          minWidth: 100,
          borderRadius: (theme) => theme.shape.borderRadius,
          typography: "caption",
          fontWeight: 400,
          lineHeight: "16px",
          textAlign: "center",
          whiteSpace: "nowrap",
          bgcolor: active ? "primary.main" : "background.paper",
          color: active ? "primary.contrastText" : "text.primary",
          boxShadow: 0,
        }}
      >
        {label ?? ""}
      </Box>
    </EdgeLabelRenderer>
  )
}

export default CustomEdgeLabel
