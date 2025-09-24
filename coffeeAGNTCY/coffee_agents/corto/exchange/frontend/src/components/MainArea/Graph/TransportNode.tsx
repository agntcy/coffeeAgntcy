/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Handle, Position } from "@xyflow/react"

interface SlimNodeData {
  label: string
  active?: boolean
}

interface SlimNodeProps {
  data: SlimNodeData
}

const SlimNode: React.FC<SlimNodeProps> = ({ data }) => {
  const activeClasses = data.active
    ? "bg-node-background-active outline outline-2 outline-accent-border shadow-[var(--shadow-default)_0px_6px_8px]"
    : "bg-node-background"

  return (
    <div
      className={` ${activeClasses} flex items-center justify-center border border-gray-100 text-center text-gray-50 hover:bg-node-background-hover hover:shadow-[var(--shadow-default)_0px_6px_8px] hover:outline hover:outline-2 hover:outline-accent-border`}
      style={{
        width: "1200px",
        height: "52px",
        padding: "16px",
        borderRadius: "8px",
      }}
    >
      <div>{data.label}</div>
      <Handle
        type="target"
        id="top"
        position={Position.Top}
        style={{
          width: "0.1px",
          height: "0.1px",
          border: `1px solid darkgrey`,
        }}
        className="bg-node-data-background"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_left"
        style={{
          left: "25%",
          width: "0.1px",
          height: "0.1px",
          border: `1px solid darkgrey`,
        }}
        className="bg-node-data-background"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_center"
        style={{
          left: "50%",
          width: "0.1px",
          height: "0.1px",
          border: `1px solid darkgrey`,
        }}
        className="bg-node-data-background"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom_right"
        style={{
          left: "75%",
          width: "0.1px",
          height: "0.1px",
          border: `1px solid darkgrey`,
        }}
        className="bg-node-data-background"
      />
    </div>
  )
}

export default SlimNode
