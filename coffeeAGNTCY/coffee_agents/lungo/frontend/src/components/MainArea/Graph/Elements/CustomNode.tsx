/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useRef } from "react"
import { Handle, Position } from "@xyflow/react"
import { IconButton } from "@open-ui-kit/core"
import AssignmentTurnedIn from "@mui/icons-material/AssignmentTurnedIn"
import Box from "@mui/material/Box"
import githubIconLight from "@/assets/Github_lightmode.png"
import agentDirectoryIconDark from "@/assets/Agent_directory.png"
import agentDirectoryIconLight from "@/assets/Agent_Icon_light.png"
import identityBadgeIcon from "@/assets/identity_badge.svg"
import { useThemeIcon } from "@/hooks/useThemeIcon"
import { logger } from "@/utils/logger"
import { SecurityClass } from "@/utils/SecurityClass"
import { CustomNodeData, ExtraHandle } from "./types"

const POSITION_MAP: Record<ExtraHandle["position"], Position> = {
  top: Position.Top,
  bottom: Position.Bottom,
  left: Position.Left,
  right: Position.Right,
}

interface CustomNodeProps {
  data: CustomNodeData
  onOpenOasfModal?: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
  ) => void
}

const CustomNode: React.FC<CustomNodeProps> = ({
  data,
  //onOpenOasfModal,
}) => {
  const nodeRef = useRef<HTMLDivElement>(null)

  const githubIconSrc = githubIconLight
  const agentDirectoryIcon = useThemeIcon({
    light: agentDirectoryIconLight,
    dark: agentDirectoryIconDark,
  })

  const handleIdentityClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()

    if (nodeRef.current && data.onOpenIdentityModal) {
      const buttonRect = (
        e.currentTarget as HTMLElement
      ).getBoundingClientRect()
      const isMcpServer = data.label1?.includes("MCP Server")
      let position
      if (isMcpServer) {
        position = {
          x: buttonRect.right + 12,
          y: buttonRect.top + buttonRect.height / 2,
        }
      } else {
        const buttonCenterX = buttonRect.left + buttonRect.width / 2
        position = {
          x: buttonCenterX,
          y: buttonRect.bottom + 12,
        }
      }
      data.onOpenIdentityModal(
        data,
        position,
        data.label1 || "",
        data,
        isMcpServer,
      )
    } else {
      logger.error("No modal handler found or nodeRef missing!")
    }
  }

  const handleAgentDirectoryClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (nodeRef.current && typeof data.onOpenOasfModal === "function") {
      const buttonRect = (
        e.currentTarget as HTMLElement
      ).getBoundingClientRect()
      const buttonCenterX = buttonRect.left + buttonRect.width / 2
      const position = {
        x: buttonCenterX,
        y: buttonRect.bottom + 12,
      }
      data.onOpenOasfModal(data, position)
    }
  }

  const activeClasses = data.active
    ? "bg-node-background-active outline outline-2 outline-accent-border shadow-[var(--shadow-default)_0px_6px_8px]"
    : data.selected
      ? "bg-node-background outline outline-2 outline-accent-primary shadow-[var(--shadow-default)_0px_6px_8px]"
      : "bg-node-background"

  return (
    <>
      <div
        ref={nodeRef}
        className={`order-0 relative flex h-[91px] w-[193px] flex-none grow-0 flex-col items-start justify-start gap-2 rounded-lg p-4 ${activeClasses} hover:bg-node-background-hover hover:shadow-[var(--shadow-default)_0px_6px_8px] hover:outline hover:outline-2 hover:outline-accent-border`}
      >
        <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center gap-2.5 rounded bg-node-icon-background py-1 opacity-100">
          <div className="flex h-4 w-4 items-center justify-center opacity-100">
            {data.icon}
          </div>
        </div>

        <div
          className="order-0 flex h-5 flex-none grow-0 flex-row items-center gap-1 self-stretch p-0"
          style={{
            width: data.verificationStatus === "verified" ? "160px" : "162px",
          }}
        >
          <span className="order-0 flex h-5 flex-none grow-0 items-center overflow-hidden text-ellipsis whitespace-nowrap font-inter text-sm font-normal leading-5 tracking-normal text-node-text-primary opacity-100">
            {data.label1}
          </span>
          {data.verificationStatus === "verified" && (
            <Box
              component="img"
              src={identityBadgeIcon}
              alt="Verified"
              className="order-1 flex-none grow-0"
              sx={{
                width: 16,
                height: 16,
                bgcolor: "#ffffff",
              }}
            />
          )}
        </div>

        <div
          className="order-1 h-4 flex-none flex-grow-0 self-stretch overflow-hidden text-ellipsis whitespace-nowrap font-inter text-xs font-light leading-4 text-node-text-secondary"
          style={{
            width: "162px",
          }}
        >
          {data.label2}
        </div>

        <div className="absolute -right-4 top-1/2 z-10 flex -translate-y-1/2 flex-col gap-1">
          {data.githubLink &&
            SecurityClass.isSafeExternalUrl(data.githubLink) && (
              <IconButton
                component="a"
                href={data.githubLink}
                target="_blank"
                rel="noopener noreferrer"
                size="small"
                aria-label="Open GitHub repository"
                sx={{
                  width: 28,
                  height: 28,
                  boxShadow: 1,
                  "&:hover": { opacity: 0.8 },
                }}
              >
                <Box
                  component="img"
                  src={githubIconSrc}
                  alt=""
                  sx={{
                    width: 20,
                    height: 20,
                    bgcolor: "#ffffff",
                  }}
                />
              </IconButton>
            )}
          {data.agentDirectoryLink && (
            <IconButton
              type="button"
              size="small"
              aria-label="Open AGNTCY Directory"
              onClick={handleAgentDirectoryClick}
              sx={{
                width: 28,
                height: 28,
                boxShadow: 1,
                "&:hover": { opacity: 0.8 },
              }}
            >
              <Box
                component="img"
                src={agentDirectoryIcon}
                alt=""
                sx={{
                  width: 20,
                  height: 20,
                  bgcolor: "#ffffff",
                }}
              />
            </IconButton>
          )}
          {data.verificationStatus === "verified" && (
            <IconButton
              type="button"
              size="small"
              aria-label="Open identity details"
              onClick={handleIdentityClick}
              sx={{
                width: 28,
                height: 28,
                boxShadow: 1,
                "&:hover": {
                  opacity: data.isModalOpen === true ? 1 : 0.8,
                },
              }}
            >
              <AssignmentTurnedIn
                sx={{
                  fontSize: 20,
                }}
              />
            </IconButton>
          )}
        </div>

        {(data.handles === "all" || data.handles === "target") && (
          <Handle
            type="target"
            position={Position.Top}
            id="target"
            className="h-px w-px border border-gray-600 bg-node-data-background"
          />
        )}
        {(data.handles === "all" || data.handles === "source") && (
          <Handle
            type="source"
            position={Position.Bottom}
            id="source"
            className="h-px w-px border border-gray-600 bg-node-data-background"
          />
        )}
        {data.extraHandles?.map((eh) => (
          <Handle
            key={eh.id}
            type={eh.type}
            position={POSITION_MAP[eh.position]}
            id={eh.id}
            className="h-px w-px border border-gray-600 bg-node-data-background"
          />
        ))}
      </div>
    </>
  )
}

export default CustomNode
