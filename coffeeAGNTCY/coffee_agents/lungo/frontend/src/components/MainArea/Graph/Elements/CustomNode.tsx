/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef } from "react"
import { Handle, Position } from "@xyflow/react"
import AssignmentTurnedIn from "@mui/icons-material/AssignmentTurnedIn"
import { Box, IconButton, Stack, Typography, useTheme } from "@open-ui-kit/core"
import githubIconLight from "@/assets/Github_lightmode.png"
import agentDirectoryIconDark from "@/assets/Agent_directory.png"
import agentDirectoryIconLight from "@/assets/Agent_Icon_light.png"
import identityBadgeIcon from "@/assets/identity_badge.svg"
import { useThemeIcon } from "@/hooks/useThemeIcon"
import { logger } from "@/utils/logger"
import { SecurityClass } from "@/utils/SecurityClass"
import {
  getGraphNodeHandleStyle,
  graphNodeIconSlotSx,
  graphNodeRootSurfaceSx,
  graphNodeSideIconButtonSx,
  graphNodeSideIconButtonSxWithModal,
  type GraphNodeSurfaceState,
} from "./graphNodeSurface"
import { CustomNodeData, ExtraHandle } from "./types"

const POSITION_MAP: Record<ExtraHandle["position"], Position> = {
  top: Position.Top,
  bottom: Position.Bottom,
  left: Position.Left,
  right: Position.Right,
}

interface CustomNodeProps {
  data: CustomNodeData
}

const CustomNode: React.FC<CustomNodeProps> = ({ data }) => {
  const nodeRef = useRef<HTMLDivElement>(null)
  const theme = useTheme()

  // TODO: set both dark and light mode of github icon here
  const githubIconSrc = githubIconLight
  const agentDirectoryIcon = useThemeIcon({
    light: agentDirectoryIconLight,
    dark: agentDirectoryIconDark,
  })

  const surfaceState: GraphNodeSurfaceState = data.active
    ? "active"
    : data.selected
      ? "selected"
      : "default"

  const handleStyle = getGraphNodeHandleStyle(theme)

  const handleIdentityClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()

    if (nodeRef.current && data.onOpenIdentityModal) {
      data.onOpenIdentityModal(data, data.label1 || "", data)
    } else {
      logger.error("No modal handler found or nodeRef missing!")
    }
  }

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
          width: 193,
          flexGrow: 0,
          flexShrink: 0,
          order: 0,
        })}
      >
        <Box
          sx={(t) => ({
            display: "flex",
            width: 20,
            height: 20,
            flexShrink: 0,
            alignItems: "center",
            justifyContent: "center",
            py: 0.5,
            ...graphNodeIconSlotSx(t),
          })}
        >
          <Box
            sx={{
              display: "flex",
              width: 16,
              height: 16,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {data.icon}
          </Box>
        </Box>

        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            gap: 0.5,
            alignSelf: "stretch",
            p: 0,
            order: 0,
            flexGrow: 0,
            flexShrink: 0,
            height: 20,
            width: data.verificationStatus === "verified" ? 160 : 162,
          }}
        >
          <Typography
            variant="body2"
            component="span"
            noWrap
            sx={{
              flex: "1 1 auto",
              minWidth: 0,
              fontWeight: 400,
              letterSpacing: "normal",
              lineHeight: "20px",
            }}
          >
            {data.label1}
          </Typography>
          {data.verificationStatus === "verified" && (
            <Box
              component="img"
              src={identityBadgeIcon}
              alt="Verified"
              sx={(t) => ({
                flexShrink: 0,
                flexGrow: 0,
                order: 1,
                bgcolor: t.palette.common.white,
              })}
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
            width: 162,
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
              <IconButton
                component="a"
                href={data.githubLink}
                target="_blank"
                rel="noopener noreferrer"
                size="small"
                aria-label="Open GitHub repository"
                sx={(t) => ({
                  ...graphNodeSideIconButtonSx(t),
                })}
              >
                <Box
                  component="img"
                  src={githubIconSrc}
                  alt="GitHub"
                  sx={(t) => ({
                    width: 20,
                    height: 20,
                    bgcolor: t.palette.common.white,
                  })}
                />
              </IconButton>
            )}
          {data.agentDirectoryLink && (
            <IconButton
              type="button"
              size="small"
              aria-label="Open AGNTCY Directory"
              onClick={handleAgentDirectoryClick}
              sx={(t) => ({
                ...graphNodeSideIconButtonSx(t),
              })}
            >
              <Box
                component="img"
                src={agentDirectoryIcon}
                alt="AGNTCY Directory"
                sx={(t) => ({
                  width: 20,
                  height: 20,
                  bgcolor: t.palette.common.white,
                })}
              />
            </IconButton>
          )}
          {data.verificationStatus === "verified" && (
            <IconButton
              type="button"
              size="small"
              aria-label="Open identity details"
              onClick={handleIdentityClick}
              sx={(t) => ({
                ...graphNodeSideIconButtonSxWithModal(
                  t,
                  data.isModalOpen === true,
                ),
              })}
            >
              <AssignmentTurnedIn
                sx={{
                  fontSize: 20,
                }}
              />
            </IconButton>
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
