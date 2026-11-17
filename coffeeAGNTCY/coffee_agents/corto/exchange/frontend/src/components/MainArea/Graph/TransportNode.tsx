/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"
import { Box, OverflowTooltip, Typography, useTheme } from "@open-ui-kit/core"
import {
  getGraphNodeHandleStyle,
  graphNodeRootSurfaceSx,
} from "./Elements/nodes/graphNodeSurface"

interface SlimNodeData {
  label: string
  active?: boolean
}

interface SlimNodeProps {
  data: SlimNodeData
}

const SlimNode: React.FC<SlimNodeProps> = ({ data }) => {
  const theme = useTheme()
  const handleStyle = getGraphNodeHandleStyle(theme)

  return (
    <Box
      sx={(t) => ({
        ...graphNodeRootSurfaceSx(t, { active: data.active }),
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        textAlign: "center",
        width: 1200,
        height: 52,
      })}
    >
      <Box sx={{ flex: 1, minWidth: 0, textAlign: "center" }}>
        <OverflowTooltip value={data.label}>
          <Typography variant="h6" component="span">
            {data.label}
          </Typography>
        </OverflowTooltip>
      </Box>
      <Handle
        type="target"
        id="top"
        position={Position.Top}
        style={handleStyle}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_left"
        style={{ ...handleStyle, left: "25%" }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_center"
        style={{ ...handleStyle, left: "50%" }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_right"
        style={{ ...handleStyle, left: "75%" }}
      />
    </Box>
  )
}

export default SlimNode
