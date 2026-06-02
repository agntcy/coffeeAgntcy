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
  graphNodeAuxiliaryControlSurfaceSx,
  graphNodeRootSurfaceSx,
} from "./graphNodeSurface"
import { TransportNodeData } from "./types"

interface TransportNodeProps {
  data: TransportNodeData
}

const TransportNode: React.FC<TransportNodeProps> = ({ data }) => {
  const theme = useTheme()
  const githubIconSrc = useGithubIcon()

  const isCircular = data.compact
  const handleStyle: CSSProperties = getGraphNodeHandleStyle(theme)

  return (
    <Box
      sx={(t) => ({
        ...graphNodeRootSurfaceSx(t, data.active ? "active" : "default", {
          borderRadius: isCircular ? "50%" : undefined,
        }),
        position: "relative",
        display: "flex",
        flexDirection: isCircular ? "column" : "row",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        textAlign: "center",
        width: isCircular ? 120 : 1200,
        height: isCircular ? 120 : 52,
      })}
    >
      <Typography
        component="div"
        variant={isCircular ? "caption" : "body2"}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          whiteSpace: "nowrap",
          textAlign: "center",
          fontWeight: 400,
          letterSpacing: "normal",
          ...(isCircular && !data.githubLink ? { mb: 1 } : {}),
          ...(!isCircular
            ? {
                height: 20,
                width: 94,
                minWidth: 0,
              }
            : {}),
        }}
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
              ...graphNodeAuxiliaryControlSurfaceSx(t),
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
              top: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 + 50 * Math.sin(Math.PI / 4)}px`,
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
              bottom: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 + 50 * Math.sin(Math.PI / 4)}px`,
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
              bottom: `${60 - 50 * Math.cos(Math.PI / 4)}px`,
              left: `${60 - 50 * Math.sin(Math.PI / 4)}px`,
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
