/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Position, getBezierPath, useStore, Node } from "@xyflow/react"
import CustomEdgeLabel from "./CustomEdgeLabel"

interface BranchingEdgeData {
  active?: boolean
  label?: string
  branches?: string[]
}

interface BranchingEdgeProps {
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: Position
  targetPosition: Position
  data?: BranchingEdgeData
}

const BranchingEdge: React.FC<BranchingEdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}) => {
  const defaultEdgeColor = data?.active ? "#00409F" : "#00409F"

  const nodes = useStore((store) => Array.from(store.nodeLookup.values()))

  if (!data?.branches || data.branches.length === 0) {
    const [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    })

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
        <path
          id={id}
          d={edgePath}
          markerStart={`url(#${id}-arrow-start)`}
          markerEnd={`url(#${id}-arrow-end)`}
          className="react-flow__edge-path cursor-pointer"
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

  const branchY = sourceY + 60
  const branchX = sourceX

  const [trunkPath, trunkLabelX, trunkLabelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX: branchX,
    targetY: branchY,
    targetPosition: Position.Top,
  })

  const branchPaths = data.branches
    .map((nodeId: string) => {
      const targetNode = nodes.find((node: Node) => node.id === nodeId)
      if (!targetNode) return null

      let absoluteX = targetNode.position.x
      let absoluteY = targetNode.position.y

      if (targetNode.parentId) {
        const parentNode = nodes.find(
          (node: Node) => node.id === targetNode.parentId,
        )
        if (parentNode) {
          absoluteX += parentNode.position.x
          absoluteY += parentNode.position.y
        }
      }

      const targetNodeX = absoluteX + (targetNode.measured?.width ?? 200) / 2
      const targetNodeY = absoluteY

      const [branchPath, labelX, labelY] = getBezierPath({
        sourceX: branchX,
        sourceY: branchY,
        sourcePosition: Position.Bottom,
        targetX: targetNodeX,
        targetY: targetNodeY,
        targetPosition: Position.Top,
      })

      return {
        path: branchPath,
        nodeId,
        labelX,
        labelY,
      }
    })
    .filter(Boolean)

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

      <path
        d={trunkPath}
        markerStart={`url(#${id}-arrow-start)`}
        className="react-flow__edge-path cursor-pointer"
        style={{
          stroke: defaultEdgeColor,
          strokeWidth: 1,
        }}
      />

      <circle
        cx={branchX}
        cy={branchY}
        r={3}
        fill={defaultEdgeColor}
        className="react-flow__edge-path"
      />

      {branchPaths.map((branch, index) =>
        branch ? (
          <path
            key={`branch-${branch.nodeId}-${index}`}
            d={branch.path}
            markerEnd={`url(#${id}-arrow-end)`}
            className="react-flow__edge-path cursor-pointer"
            style={{
              stroke: defaultEdgeColor,
              strokeWidth: 1,
            }}
          />
        ) : null,
      )}

      <CustomEdgeLabel
        x={trunkLabelX}
        y={trunkLabelY}
        label={data?.label}
        active={data?.active}
      />
    </>
  )
}

export default BranchingEdge
