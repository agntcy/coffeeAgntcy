/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"
import { DefaultHandleColor } from "./CustomNode"
import githubIcon from "@/assets/Github.png"

interface TransportNodeData {
  label: string
  active?: boolean
  handleColor?: string
  githubLink?: string
}

interface TransportNodeProps {
  data: TransportNodeData
}

const TransportNode: React.FC<TransportNodeProps> = ({ data }) => {
  const activeClasses = data.active
    ? "bg-[#00142B] outline outline-2 outline-[#187ADC] shadow-[rgba(0,0,0,0.6)_0px_6px_8px]"
    : "bg-[#373C42]"

  return (
    <div
      className={` ${activeClasses} relative flex h-[52px] w-[1200px] items-center justify-center rounded-lg p-4 text-center text-gray-50 hover:bg-[#4A4F55] hover:shadow-[rgba(0,0,0,0.6)_0px_6px_8px] hover:outline hover:outline-2 hover:outline-[#187ADC]`}
    >
      <div className="flex h-5 w-[94px] items-center justify-center whitespace-nowrap font-inter text-sm font-normal leading-5 tracking-normal text-[#E8E9EA] opacity-100">
        {data.label}
      </div>

      {/* GitHub Icon */}
      {data.githubLink && (
        <a
          href={data.githubLink}
          target="_blank"
          rel="noopener noreferrer"
          className="no-underline"
        >
          <div
            className="absolute -right-4 top-1/2 z-10 flex h-7 w-7 -translate-y-1/2 cursor-pointer items-center justify-center rounded-lg bg-[#00142B] p-1 opacity-100 shadow-sm transition-opacity duration-200 ease-in-out"
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

      <Handle
        type="target"
        id="top"
        position={Position.Top}
        className="h-[0.1px] w-[0.1px] border border-gray-600"
        style={{
          background: data.handleColor || DefaultHandleColor,
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_left"
        className="h-[0.1px] w-[0.1px] border border-gray-600"
        style={{
          left: "25%",
          background: data.handleColor || DefaultHandleColor,
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_center"
        className="h-[0.1px] w-[0.1px] border border-gray-600"
        style={{
          left: "50%",
          background: data.handleColor || DefaultHandleColor,
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_right"
        className="h-[0.1px] w-[0.1px] border border-gray-600"
        style={{
          left: "75%",
          background: data.handleColor || DefaultHandleColor,
        }}
      />
    </div>
  )
}

export default TransportNode
