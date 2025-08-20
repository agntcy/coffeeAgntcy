/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { EdgeLabelRenderer } from "@xyflow/react"
import { cn } from "@/lib/utils.ts"

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
  const isSlimLabel = label?.includes("SLIM")
  const isValidateLabel = label?.toLowerCase().includes("validate")
  const isLongLabel = isSlimLabel || isValidateLabel

  const backgroundColor = active ? "#00142B" : "#183056"
  const textColor = active ? "#187ADC" : "#E8E9EA"

  return (
    <EdgeLabelRenderer>
      <div
        className={cn(
          "pointer-events-none absolute -translate-x-1/2 -translate-y-1/2",
          "h-5 rounded-lg px-[5px] py-[2px] font-inter text-xs font-normal leading-4",
          "flex items-center justify-center border-none opacity-100 shadow-none",
          isLongLabel ? "w-[100px] gap-[6px]" : "w-[34px] gap-1",
        )}
        style={{
          left: `${x}px`,
          top: `${y}px`,
          backgroundColor,
          color: textColor,
        }}
      >
        {label && (
          <div
            className={cn(
              "flex flex-shrink-0 items-center justify-center whitespace-nowrap",
              "font-inter text-xs font-normal leading-4",
            )}
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
