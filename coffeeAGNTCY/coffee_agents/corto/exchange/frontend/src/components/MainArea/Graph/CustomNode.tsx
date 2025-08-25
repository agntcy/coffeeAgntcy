/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"
import githubIcon from "@/assets/Github.png"
import agentDirectoryIcon from "@/assets/Agent_directory.png"

export const DefaultHandleColor = "#f5f5f5"

interface CustomNodeData {
  icon: React.ReactNode
  label1: string
  label2: string
  active?: boolean
  handleColor?: string
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
  const activeClasses = data.active
    ? "bg-[#00142B] outline outline-2 outline-[#187ADC] shadow-[rgba(0,0,0,0.6)_0px_6px_8px]"
    : "bg-[#373C42]"

  return (
    <div
      className={`order-0 relative flex h-[91px] w-[193px] flex-none grow-0 flex-col items-start justify-start gap-2 rounded-lg p-4 ${activeClasses} hover:bg-[#4A4F55] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px] hover:outline hover:outline-2 hover:outline-[#187ADC]`}
    >
      <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center gap-2.5 rounded bg-[#59616B] py-1 opacity-100">
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
        <span className="order-0 flex h-5 flex-none grow-0 items-center overflow-hidden text-ellipsis whitespace-nowrap font-inter text-sm font-normal leading-5 tracking-normal text-[#E8E9EA] opacity-100">
          {data.label1}
        </span>
      </div>

      <div
        className="order-1 h-4 flex-none flex-grow-0 self-stretch overflow-hidden text-ellipsis whitespace-nowrap font-inter text-xs font-light leading-4 text-[#E8E9EA]"
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
            style={{
              textDecoration: "none",
            }}
          >
            <div
              className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg bg-[#00142B] p-1 opacity-100 shadow-sm transition-opacity duration-200 ease-in-out"
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "0.8"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "1"
              }}
            >
              <img src={githubIcon} alt="GitHub" className="h-5 w-5" />
            </div>
          </a>
        )}

        {data.agentDirectoryLink && (
          <a
            href={data.agentDirectoryLink}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: "none",
            }}
          >
            <div
              className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg bg-[#00142B] p-1 opacity-100 shadow-sm"
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
          className="h-[0.1px] w-[0.1px] border border-gray-600"
          style={{
            background: data.handleColor || DefaultHandleColor,
          }}
        />
      )}
      {(data.handles === "all" || data.handles === "source") && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="source"
          className="h-[0.1px] w-[0.1px] border border-gray-600"
          style={{
            background: data.handleColor || DefaultHandleColor,
          }}
        />
      )}
    </div>
  )
}

export default CustomNode
