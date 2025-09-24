/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"
import githubIcon from "@/assets/Github.png"
import githubIconLight from "@/assets/Github_lightmode.png"
import agentDirectoryIconDark from "@/assets/Agent_directory.png"
import agentDirectoryIconLight from "@/assets/Agent_Icon_light.png"
import identityBadgeIcon from "@/assets/identity_badge.svg"
import { useThemeIcon } from "@/hooks/useThemeIcon"

interface CustomNodeData {
  icon: React.ReactNode
  label1: string
  label2: string
  active?: boolean
  handles?: "all" | "target" | "source"
  verificationStatus?: "verified" | "failed" | "pending"
  verificationBadge?: React.ReactNode
  githubLink?: string
  agentDirectoryLink?: string
}

interface CustomNodeProps {
  data: CustomNodeData
}

const CustomNode: React.FC<CustomNodeProps> = ({ data }) => {
  const githubIconSrc = useThemeIcon({
    light: githubIconLight,
    dark: githubIcon,
  })
  const agentDirectoryIcon = useThemeIcon({
    light: agentDirectoryIconLight,
    dark: agentDirectoryIconDark,
  })

  const activeClasses = data.active
    ? "bg-node-background-active outline outline-2 outline-accent-border shadow-[var(--shadow-default)_0px_6px_8px]"
    : "bg-node-background"

  return (
    <div
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
          <img
            src={identityBadgeIcon}
            alt="Verified"
            className="order-1 h-4 w-4 flex-none grow-0"
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
        {data.githubLink && (
          <a
            href={data.githubLink}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline"
          >
            <div
              className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg border border-solid p-1 opacity-100 shadow-sm transition-opacity duration-200 ease-in-out"
              style={{
                backgroundColor: "var(--custom-node-background)",
                borderColor: "var(--custom-node-border)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "0.8"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "1"
              }}
            >
              <img src={githubIconSrc} alt="GitHub" className="h-5 w-5" />
            </div>
          </a>
        )}
        {data.agentDirectoryLink && (
          <a
            href={data.agentDirectoryLink}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline"
          >
            <div
              className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg border border-solid p-1 opacity-100 shadow-sm"
              style={{
                backgroundColor: "var(--custom-node-background)",
                borderColor: "var(--custom-node-border)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "0.8"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "1"
              }}
            >
              <img
                src={agentDirectoryIcon}
                alt="AGNTCY Directory"
                className="h-5 w-5"
              />
            </div>
          </a>
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
    </div>
  )
}

export default CustomNode
