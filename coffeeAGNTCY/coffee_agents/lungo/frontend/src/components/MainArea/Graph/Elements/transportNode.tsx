/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { type CSSProperties } from "react"
import { Handle, Position } from "@xyflow/react"
import { Box, Typography, useTheme } from "@open-ui-kit/core"
import { GraphSideIconTooltip } from "./GraphSideIconTooltip"
import { useGithubIcon } from "@/hooks/useGithubIcon"
import { AssetPngIcon } from "@/components/AssetPngIcon"
import { SecurityClass } from "@/utils/SecurityClass"
import {
  getGraphNodeHandleStyle,
  graphNodeSideIconLinkSx,
  graphNodeRootSurfaceSx,
} from "./graphNodeSurface"
import { TransportNodeData } from "./types"

interface TransportNodeProps {
  data: TransportNodeData
}

/** Circular compact transport node — keep handle geometry in sync with width/height. */
const CIRCULAR_TRANSPORT_NODE_SIZE = 176
const CIRCULAR_NODE_CENTER = CIRCULAR_TRANSPORT_NODE_SIZE / 2
const CIRCULAR_NODE_RADIUS = CIRCULAR_NODE_CENTER
const CIRCULAR_DIAGONAL_SIN = Math.sin(Math.PI / 4)
const CIRCULAR_DIAGONAL_COS = Math.cos(Math.PI / 4)

function circularDiagonalHandlePosition(
  quadrant: "top_left" | "top_right" | "bottom_left" | "bottom_right",
): Pick<CSSProperties, "top" | "bottom" | "left"> {
  const offset = CIRCULAR_NODE_RADIUS * CIRCULAR_DIAGONAL_SIN
  const axial = CIRCULAR_NODE_RADIUS * CIRCULAR_DIAGONAL_COS

  switch (quadrant) {
    case "top_right":
      return {
        top: `${CIRCULAR_NODE_CENTER - axial}px`,
        left: `${CIRCULAR_NODE_CENTER + offset}px`,
      }
    case "top_left":
      return {
        top: `${CIRCULAR_NODE_CENTER - axial}px`,
        left: `${CIRCULAR_NODE_CENTER - offset}px`,
      }
    case "bottom_right":
      return {
        bottom: `${CIRCULAR_NODE_CENTER - axial}px`,
        left: `${CIRCULAR_NODE_CENTER + offset}px`,
      }
    case "bottom_left":
      return {
        bottom: `${CIRCULAR_NODE_CENTER - axial}px`,
        left: `${CIRCULAR_NODE_CENTER - offset}px`,
      }
  }
}

const TransportNode: React.FC<TransportNodeProps> = ({ data }) => {
  const theme = useTheme()
  const githubIconSrc = useGithubIcon()

  const isCircular = data.compact
  const handleStyle: CSSProperties = getGraphNodeHandleStyle(theme)

  return (
    <Box
      sx={(t) => ({
        ...graphNodeRootSurfaceSx(
          t,
          { active: data.active },
          {
            borderRadius: isCircular ? "50%" : undefined,
          },
        ),
        position: "relative",
        display: "flex",
        flexDirection: isCircular ? "column" : "row",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        textAlign: "center",
        width: isCircular ? CIRCULAR_TRANSPORT_NODE_SIZE : 1200,
        height: isCircular ? CIRCULAR_TRANSPORT_NODE_SIZE : 52,
      })}
    >
      <Typography
        component="div"
        variant="h6"
        sx={() => ({
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          whiteSpace: "nowrap",
          textAlign: "center",
          ...(isCircular && !data.githubLink ? { mb: 1 } : {}),
          ...(!isCircular
            ? {
                minHeight: 20,
                width: 94,
                minWidth: 0,
              }
            : {}),
        })}
      >
        {data.label}
      </Typography>

      {data.githubLink && SecurityClass.isSafeExternalUrl(data.githubLink) && (
        <GraphSideIconTooltip title="Open repository on GitHub">
          <Box
            component="a"
            href={data.githubLink}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open GitHub repository"
            sx={(t) => ({
              ...graphNodeSideIconLinkSx(t),
              ...(isCircular
                ? { mt: 0.5 }
                : {
                    position: "absolute",
                    right: -16,
                    top: "50%",
                    transform: "translateY(-50%)",
                    zIndex: 10,
                  }),
            })}
          >
            <AssetPngIcon bare src={githubIconSrc} alt="GitHub" />
          </Box>
        </GraphSideIconTooltip>
      )}

      {isCircular ? (
        <>
          <Handle
            type="target"
            id="top"
            position={Position.Top}
            style={{
              ...handleStyle,
              top: "8px",
              left: "50%",
              transform: "translateX(-50%)",
            }}
          />
          <Handle
            type="target"
            id="top_right"
            position={Position.Top}
            style={{
              ...handleStyle,
              ...circularDiagonalHandlePosition("top_right"),
            }}
          />
          <Handle
            type="target"
            id="right"
            position={Position.Right}
            style={{
              ...handleStyle,
              right: "8px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_right"
            style={{
              ...handleStyle,
              ...circularDiagonalHandlePosition("bottom_right"),
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_center"
            style={{
              ...handleStyle,
              bottom: "8px",
              left: "50%",
              transform: "translateX(-50%)",
            }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_left"
            style={{
              ...handleStyle,
              ...circularDiagonalHandlePosition("bottom_left"),
            }}
          />
          <Handle
            type="target"
            id="left"
            position={Position.Left}
            style={{
              ...handleStyle,
              left: "8px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          />
          <Handle
            type="target"
            id="top_left"
            position={Position.Top}
            style={{
              ...handleStyle,
              ...circularDiagonalHandlePosition("top_left"),
            }}
          />
        </>
      ) : (
        <>
          <Handle
            type="target"
            id="top"
            position={Position.Top}
            style={handleStyle}
          />
          <Handle
            type="target"
            id="top_left"
            position={Position.Top}
            style={{ ...handleStyle, left: "30%" }}
          />
          <Handle
            type="target"
            id="top_center"
            position={Position.Top}
            style={{ ...handleStyle, left: "50%" }}
          />
          <Handle
            type="target"
            id="top_right"
            position={Position.Top}
            style={{ ...handleStyle, left: "70%" }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_left"
            style={{ ...handleStyle, left: "30%" }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_center"
            style={{ ...handleStyle, left: "50%" }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom_right"
            style={{ ...handleStyle, left: "70%" }}
          />
        </>
      )}
    </Box>
  )
}

export default TransportNode
