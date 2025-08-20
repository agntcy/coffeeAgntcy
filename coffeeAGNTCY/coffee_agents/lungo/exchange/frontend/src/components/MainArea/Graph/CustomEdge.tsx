/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { getBezierPath, BaseEdge, Position } from "@xyflow/react"
import CustomEdgeLabel from "./CustomEdgeLabel"

interface CustomEdgeData {
  active?: boolean
  label?: string
  labelIconType?: string
}

interface CustomEdgeProps {
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: Position
  targetPosition: Position
  data?: CustomEdgeData
}

const CustomEdge: React.FC<CustomEdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const defaultEdgeColor = data?.active ? "#187ADC" : "#B0C4DE"

  return (
    <>
      <svg className="absolute left-0 top-0">
        <defs>
          <marker
            id={`${id}-arrow-start`}
            markerWidth="5"
            markerHeight="5"
            refX="0.5"
            refY="2.5"
            orient="auto"
          >
            <path d="M5,0 L0,2.5 L5,5 Z" fill={defaultEdgeColor} />
          </marker>
          <marker
            id={`${id}-arrow-end`}
            markerWidth="5"
            markerHeight="5"
            refX="4.5"
            refY="2.5"
            orient="auto"
          >
            <path d="M0,0 L5,2.5 L0,5 Z" fill={defaultEdgeColor} />
          </marker>
        </defs>
      </svg>
      <BaseEdge
        id={id}
        path={edgePath}
        markerStart={`url(#${id}-arrow-start)`}
        markerEnd={`url(#${id}-arrow-end)`}
        className="cursor-pointer"
        style={{
          stroke: defaultEdgeColor,
          strokeWidth: 1,
        }}
      />
      <CustomEdgeLabel
        x={labelX}
        y={labelY}
        label={data?.label}
        active={data?.active}
      />
    </>
  )
}

export default CustomEdge
