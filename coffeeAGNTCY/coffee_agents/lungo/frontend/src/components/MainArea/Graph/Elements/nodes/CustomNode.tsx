/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef, useState } from "react"
import { Handle, Position } from "@xyflow/react"
import {
  Box,
  IconButton,
  Icons,
  Stack,
  Tooltip,
  Typography,
  useTheme,
} from "@open-ui-kit/core"
import { SecurityClass } from "@/utils/SecurityClass"
import { getSuccessIconColor } from "@/utils/successIconColor"
import {
  getGraphNodeHandleStyle,
  graphNodeDirectoryIconControlSx,
  graphNodeRootSurfaceSx,
  graphNodeSideIconControlSx,
} from "./graphNodeSurface"
import { DirectoryAIcon } from "./DirectoryAIcon"
import { GraphIconChip } from "./GraphIconChip"
import { GraphSideIconTooltip } from "./GraphSideIconTooltip"
import NodeIdentityDropdown from "../../Identity/NodeIdentityDropdown"
import {
  CUSTOM_NODE_HEIGHT,
  CUSTOM_NODE_WIDTH,
  GRAPH_NODE_PADDING_Y,
} from "@/utils/graphNodeDimensions"
import { CustomNodeData, ExtraHandle } from "./types"
import TransportRail from "../transport/TransportRail"
import { railBackgroundImage } from "../transport/transportRailBackground"
import {
  customNodeInnerWidth,
  graphNodePaddingX,
  hasGraphNodeTransportRail,
} from "./graphNodeTransportRailLayout"

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
  const [nodeHovered, setNodeHovered] = useState(false)
  const theme = useTheme()
  const handleStyle = getGraphNodeHandleStyle(theme)
  const railGradient = railBackgroundImage(
    data.transportInterfaces,
    data.activeTransport,
    theme,
  )
  const hasTransportRail = hasGraphNodeTransportRail(data.transportInterfaces)
  const paddingX = graphNodePaddingX(data.transportInterfaces)
  const innerWidth = customNodeInnerWidth(data.transportInterfaces)

  const handleAgentDirectoryClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (nodeRef.current && typeof data.onOpenOasfDialog === "function") {
      data.onOpenOasfDialog(data)
    }
  }

  return (
    <>
      <Box
        ref={nodeRef}
        component="div"
        onMouseEnter={() => setNodeHovered(true)}
        onMouseLeave={() => setNodeHovered(false)}
        sx={(t) => ({
          ...graphNodeRootSurfaceSx(t, {
            active: data.active,
            selected: data.selected,
          }),
          ...(railGradient
            ? {
                backgroundImage: railGradient,
                backgroundSize: "8px 100%",
                backgroundPosition: "left top",
                backgroundRepeat: "no-repeat",
              }
            : {}),
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "flex-start",
          gap: t.spacing(1),
          px: paddingX,
          py: GRAPH_NODE_PADDING_Y,
          boxSizing: "border-box",
          width: CUSTOM_NODE_WIDTH,
          height: CUSTOM_NODE_HEIGHT,
          flexGrow: 0,
          flexShrink: 0,
          order: 0,
        })}
      >
        {hasTransportRail && (
          <TransportRail
            transports={data.transportInterfaces!}
            expanded={nodeHovered}
            activeTransport={data.activeTransport}
          />
        )}

        <Box sx={{ position: "relative", zIndex: 1 }}>
          <GraphIconChip>{data.icon}</GraphIconChip>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            gap: 0.5,
            p: 0,
            position: "relative",
            zIndex: 1,
          }}
        >
          <Tooltip title={data.label} arrow>
            <Typography
              variant="h6"
              component="span"
              noWrap
              sx={{ flex: "1 1 auto", minWidth: 0 }}
            >
              {data.label}
            </Typography>
          </Tooltip>
          {data.verificationStatus === "verified" && (
            <Icons.CheckCircleFilled
              aria-label="Verified"
              sx={{
                flexShrink: 0,
                flexGrow: 0,
                order: 1,
                color: getSuccessIconColor(theme),
              }}
            />
          )}
        </Box>

        <Tooltip title={data.label_subtitle} arrow>
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
              width: innerWidth,
              maxWidth: "100%",
              minWidth: 0,
              fontWeight: 300,
              lineHeight: "16px",
              position: "relative",
              zIndex: 1,
            }}
          >
            {data.label_subtitle}
          </Typography>
        </Tooltip>

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
                  <Icons.Github />
                </IconButton>
              </GraphSideIconTooltip>
            )}
          {data.agentDirectoryLink && (
            <GraphSideIconTooltip title="View OASF record in AGNTCY Directory">
              <IconButton
                type="button"
                aria-label="Open AGNTCY Directory"
                onClick={handleAgentDirectoryClick}
                sx={(t) => graphNodeDirectoryIconControlSx(t)}
              >
                <DirectoryAIcon />
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
