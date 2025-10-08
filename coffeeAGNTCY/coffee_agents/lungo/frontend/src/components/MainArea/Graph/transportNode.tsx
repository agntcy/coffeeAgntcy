/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"
import { useThemeIcon } from "@/hooks/useThemeIcon"
import githubIcon from "@/assets/Github.png"
import githubIconLight from "@/assets/Github_lightmode.png"

interface TransportNodeData {
  label: string
  active?: boolean
  githubLink?: string
  compact?: boolean
}

interface TransportNodeProps {
  data: TransportNodeData
}

const TransportNode: React.FC<TransportNodeProps> = ({ data }) => {
  const githubIconSrc = useThemeIcon({
    light: githubIconLight,
    dark: githubIcon,
  })

  const activeClasses = data.active
    ? "bg-node-background-active outline outline-2 outline-accent-border shadow-[var(--shadow-default)_0px_6px_8px]"
    : "bg-node-background"

  const isCircular = data.compact
  const shapeClasses = isCircular
    ? "h-[120px] w-[120px] flex-col rounded-full"
    : "h-[52px] w-[1200px] rounded-lg"

  return (
    <div
      className={` ${activeClasses} relative flex ${shapeClasses} items-center justify-center p-4 text-center text-gray-50 hover:bg-node-background-hover hover:shadow-[var(--shadow-default)_0px_6px_8px] hover:outline hover:outline-2 hover:outline-accent-border`}
    >
      <div
        className={`flex h-auto w-auto items-center justify-center whitespace-nowrap text-center font-inter font-normal tracking-normal text-node-text-primary opacity-100 ${isCircular ? (data.githubLink ? "text-xs leading-4" : "mb-2 text-xs leading-4") : "h-5 w-[94px] text-sm leading-5"}`}
      >
        {data.label}
      </div>

      {data.githubLink && (
        <a
          href={data.githubLink}
          target="_blank"
          rel="noopener noreferrer"
          className="no-underline"
        >
          <div
            className={`flex cursor-pointer items-center justify-center rounded-lg border border-solid p-1 opacity-100 shadow-sm transition-opacity duration-200 ease-in-out ${isCircular ? "mt-1 h-6 w-6" : "absolute -right-4 top-1/2 z-10 h-7 w-7 -translate-y-1/2"}`}
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
              src={githubIconSrc}
              alt="GitHub"
              className={isCircular ? "h-4 w-4" : "h-5 w-5"}
            />
          </div>
        </a>
      )}

      {isCircular ? (
        <>
          <Handle
            type="target"
            id="top"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              top: "8px",
              left: "50%",
              transform: "translateX(-50%)",
            }}
          />
          <Handle
            type="target"
            id="top_right"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              top: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 + 50 * Math.sin(Math.PI / 4)}px`,
            }}
          />
          <Handle
            type="target"
            id="right"
            position={Position.Right}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              right: "8px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_right"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              bottom: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 + 50 * Math.sin(Math.PI / 4)}px`,
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_center"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              bottom: "8px",
              left: "50%",
              transform: "translateX(-50%)",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_left"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              bottom: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 - 50 * Math.sin(Math.PI / 4)}px`,
            }}
          />
          <Handle
            type="target"
            id="left"
            position={Position.Left}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "8px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          />
          <Handle
            type="target"
            id="top_left"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              top: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 - 50 * Math.sin(Math.PI / 4)}px`,
            }}
          />
        </>
      ) : (
        <>
          <Handle
            type="target"
            id="top"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
          />
          <Handle
            type="target"
            id="top_left"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "30%",
            }}
          />
          <Handle
            type="target"
            id="top_center"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "50%",
            }}
          />
          <Handle
            type="target"
            id="top_right"
            position={Position.Top}
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "70%",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_left"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "30%",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_center"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "50%",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_right"
            className="h-[0.1px] w-[0.1px] border border-gray-600 bg-node-data-background"
            style={{
              left: "70%",
            }}
          />
        </>
      )}
    </div>
  )
}

export default TransportNode
