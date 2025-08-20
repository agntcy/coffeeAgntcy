/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { EdgeLabelRenderer } from "@xyflow/react"

interface CustomEdgeLabelProps {
  x: number
  y: number
  label?: string
  active?: boolean
}

const CustomEdgeLabel: React.FC<CustomEdgeLabelProps> = ({
  x,
  y,
  label,
  active,
}) => {
  const backgroundColor = active ? "#00142B" : "#183056"
  const textColor = active ? "#187ADC" : "#E8E9EA"

  const isLongLabel = true

  return (
    <EdgeLabelRenderer>
      <div
        className={`${isLongLabel ? "w-[100px] gap-[6px]" : "w-[34px] gap-1"} pointer-events-none absolute flex h-5 items-center justify-center rounded-lg border-none px-[5px] py-[2px] font-[Inter] text-xs font-normal leading-4 opacity-100 shadow-none`}
        style={{
          backgroundColor,
          color: textColor,
          transform: "translate(-50%, -50%)",
          left: `${x}px`,
          top: `${y}px`,
        }}
      >
        {label && (
          <div
            className="flex flex-shrink-0 items-center justify-center whitespace-nowrap font-[Inter] text-xs font-normal leading-4"
            style={{ color: textColor }}
          >
            {label}
          </div>
        )}
      </div>
    </EdgeLabelRenderer>
  )
}

export default CustomEdgeLabel
