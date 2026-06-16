/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef } from "react"
import { Handle, Position } from "@xyflow/react"
import CheckCircle from "@mui/icons-material/CheckCircle"
import { Box, IconButton, Stack, Typography, useTheme } from "@open-ui-kit/core"
import agentDirectoryIconDark from "@/assets/Agent_directory.png"
import agentDirectoryIconLight from "@/assets/Agent_Icon_light.png"
import { useGithubIcon } from "@/hooks/useGithubIcon"
import { useThemeIcon } from "@/hooks/useThemeIcon"
import { AssetPngIcon } from "@/components/AssetPngIcon"
import { SecurityClass } from "@/utils/SecurityClass"
import {
  getGraphNodeHandleStyle,
  graphNodeRootSurfaceSx,
  graphNodeSideIconControlSx,
  type GraphNodeSurfaceState,
} from "./graphNodeSurface"
import { GraphIconChip } from "./GraphIconChip"
import { GraphSideIconTooltip } from "./GraphSideIconTooltip"
import NodeIdentityDropdown from "../Identity/NodeIdentityDropdown"
import {
  CUSTOM_NODE_HEIGHT,
  CUSTOM_NODE_INNER_WIDTH,
  CUSTOM_NODE_WIDTH,
} from "@/utils/graphNodeDimensions"
import { CustomNodeData, ExtraHandle } from "./types"

const POSITION_MAP: Record<ExtraHandle["position"], Position> = {
  top: Position.Top,
  bottom: Position.Bottom,
  left: Position.Left,
  right: Position.Right,
}

interface CustomNodeProps {
  id: string
  data: CustomNodeData
}

const CustomNode: React.FC<CustomNodeProps> = ({ id, data }) => {
  const nodeRef = useRef<HTMLDivElement>(null)
  const theme = useTheme()

  const githubIconSrc = useGithubIcon()
  const agentDirectoryIcon = useThemeIcon({
    light: agentDirectoryIconLight,
    dark: agentDirectoryIconDark,
  })

  const surfaceState: GraphNodeSurfaceState = data.active ? "active" : "default"

  const handleStyle = getGraphNodeHandleStyle(theme)

  const handleAgentDirectoryClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (nodeRef.current && typeof data.onOpenOasfModal === "function") {
      data.onOpenOasfModal(data)
    }
  }

  return (
    <>
      <Box
        ref={nodeRef}
        component="div"
        sx={(t) => ({
          ...graphNodeRootSurfaceSx(t, surfaceState),
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "flex-start",
          gap: t.spacing(1),
          p: 2,
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
          }}
        >
          <Typography
            variant="h6"
            component="span"
            noWrap
            sx={() => ({
              flex: "1 1 auto",
              minWidth: 0,
            })}
          >
            {data.label1}
          </Typography>
          {data.verificationStatus === "verified" && (
            <CheckCircle
              aria-label="Verified"
              sx={{
                flexShrink: 0,
                flexGrow: 0,
                order: 1,
                color: "success.main",
              }}
            />
          )}
        </Box>

        <Typography
          variant="caption"
          component="div"
          noWrap
          sx={{
            order: 1,
            alignSelf: "stretch",
            flexGrow: 0,
            flexShrink: 0,
            height: 16,
            width: CUSTOM_NODE_INNER_WIDTH,
            maxWidth: "100%",
            minWidth: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            fontWeight: 300,
            lineHeight: "16px",
          }}
        >
          {data.label2}
        </Typography>

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
          {data.githubLink &&
            SecurityClass.isSafeExternalUrl(data.githubLink) && (
              <GraphSideIconTooltip title="Open repository on GitHub">
                <IconButton
                  component="a"
                  href={data.githubLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open GitHub repository"
                  sx={(t) => graphNodeSideIconControlSx(t)}
                >
                  <AssetPngIcon bare src={githubIconSrc} alt="GitHub" />
                </IconButton>
              </GraphSideIconTooltip>
            )}
          {data.agentDirectoryLink && (
            <GraphSideIconTooltip title="View OASF record in AGNTCY Directory">
              <IconButton
                type="button"
                aria-label="Open AGNTCY Directory"
                onClick={handleAgentDirectoryClick}
                sx={(t) => graphNodeSideIconControlSx(t)}
              >
                <AssetPngIcon
                  bare
                  src={agentDirectoryIcon}
                  alt="AGNTCY Directory"
                />
              </IconButton>
            </GraphSideIconTooltip>
          )}
          <NodeIdentityDropdown nodeId={id} data={data} />
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
        {data.extraHandles?.map((eh) => (
          <Handle
            key={eh.id}
            type={eh.type}
            position={POSITION_MAP[eh.position]}
            id={eh.id}
            style={handleStyle}
          />
        ))}
      </Box>
    </>
  )
}

export default CustomNode
