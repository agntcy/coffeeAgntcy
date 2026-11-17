/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import { Handle, Position } from "@xyflow/react"
import {
  Box,
  IconButton,
  Icons,
  OverflowTooltip,
  Stack,
  Typography,
  useTheme,
} from "@open-ui-kit/core"
import agentDirectoryIconDark from "@/assets/Agent_directory.png"
import agentDirectoryIconLight from "@/assets/Agent_Icon_light.png"
import { useAppThemeMode } from "@/hooks/useAppThemeMode"
import {
  getGraphNodeHandleStyle,
  graphNodeDirectoryIconControlSx,
  graphNodeRootSurfaceSx,
  graphNodeSideIconControlSx,
} from "./Elements/nodes/graphNodeSurface"
import { GraphIconChip } from "./Elements/nodes/GraphIconChip"
import { GraphSideIconTooltip } from "./Elements/nodes/GraphSideIconTooltip"
import {
  CUSTOM_NODE_HEIGHT,
  CUSTOM_NODE_WIDTH,
  GRAPH_NODE_PADDING_X,
  GRAPH_NODE_PADDING_Y,
} from "@/utils/graphNodeDimensions"

export type CustomNodeData = {
  icon: React.ReactNode
  label1: string
  label2: string
  active?: boolean
  handles?: "all" | "target" | "source"
  verificationStatus?: "verified" | "failed" | "pending"
  verificationBadge?: React.ReactNode
  githubLink?: string
  agentDirectoryLink?: string
  slug?: string
  onOpenOasfModal?: (nodeData: CustomNodeData) => void
}

interface CustomNodeProps {
  data: CustomNodeData
}

const CustomNode: React.FC<CustomNodeProps> = ({ data }) => {
  const theme = useTheme()
  const { isDarkMode } = useAppThemeMode()
  const agentDirectoryIcon = isDarkMode
    ? agentDirectoryIconDark
    : agentDirectoryIconLight
  const handleStyle = getGraphNodeHandleStyle(theme)

  const handleAgentDirectoryClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()
      if (typeof data.onOpenOasfModal === "function") {
        data.onOpenOasfModal(data)
      }
    },
    [data],
  )

  return (
    <Box
      sx={(t) => ({
        ...graphNodeRootSurfaceSx(t, { active: data.active }),
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        justifyContent: "flex-start",
        gap: t.spacing(1),
        px: GRAPH_NODE_PADDING_X,
        py: GRAPH_NODE_PADDING_Y,
        boxSizing: "border-box",
        width: CUSTOM_NODE_WIDTH,
        height: CUSTOM_NODE_HEIGHT,
        flexGrow: 0,
        flexShrink: 0,
        order: 0,
      })}
    >
      <GraphIconChip>{data.icon}</GraphIconChip>

      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: 0.5,
          p: 0,
          width: "100%",
          minWidth: 0,
        }}
      >
        <Box sx={{ flex: "1 1 auto", minWidth: 0 }}>
          <OverflowTooltip value={data.label1}>
            <Typography variant="h6" component="span">
              {data.label1}
            </Typography>
          </OverflowTooltip>
        </Box>
      </Box>

      <Box
        sx={{
          order: 1,
          alignSelf: "stretch",
          flexGrow: 0,
          flexShrink: 0,
          height: 16,
          width: "100%",
          minWidth: 0,
        }}
      >
        <OverflowTooltip value={data.label2}>
          <Typography
            variant="caption"
            component="span"
            sx={{ fontWeight: 300, lineHeight: "16px" }}
          >
            {data.label2}
          </Typography>
        </OverflowTooltip>
      </Box>

      <Stack
        direction="column"
        spacing={0.5}
        sx={{
          position: "absolute",
          right: -16,
          top: "50%",
          transform: "translateY(-50%)",
          zIndex: 10,
        }}
      >
        {data.githubLink && (
          <GraphSideIconTooltip title="Open repository on GitHub">
            <IconButton
              component="a"
              href={data.githubLink}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Open GitHub repository"
              sx={(t) => graphNodeSideIconControlSx(t)}
            >
              <Icons.Github />
            </IconButton>
          </GraphSideIconTooltip>
        )}

        {data.onOpenOasfModal && (
          <GraphSideIconTooltip title="View OASF record in AGNTCY Directory">
            <IconButton
              type="button"
              onClick={handleAgentDirectoryClick}
              aria-label="AGNTCY Directory"
              sx={(t) => graphNodeDirectoryIconControlSx(t)}
            >
              <Box
                component="img"
                src={agentDirectoryIcon}
                alt="AGNTCY Directory"
              />
            </IconButton>
          </GraphSideIconTooltip>
        )}
      </Stack>

      {(data.handles === "all" || data.handles === "target") && (
        <Handle
          type="target"
          position={Position.Top}
          id="target"
          style={handleStyle}
        />
      )}
      {(data.handles === "all" || data.handles === "source") && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="source"
          style={handleStyle}
        />
      )}
    </Box>
  )
}

export default CustomNode
