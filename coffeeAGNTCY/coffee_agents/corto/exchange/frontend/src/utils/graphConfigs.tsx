/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Node, Edge } from "@xyflow/react"
import { Box } from "@open-ui-kit/core"
import supervisorIcon from "@/assets/supervisor.png"
import graderIcon from "@/assets/Grader-Agent.png"
import {
  assetPngIconBareSx,
  assetPngIconMonochromeDarkFilterSx,
} from "@/utils/assetPngIcon"

export interface GraphConfig {
  title: string
  nodes: Node[]
  edges: Edge[]
  animationSequence: { ids: string[] }[]
}

const GraderAgentIcon = (
  <Box
    component="img"
    src={graderIcon}
    alt="Grader Agent Icon"
    sx={assetPngIconBareSx(assetPngIconMonochromeDarkFilterSx())}
  />
)

const SLIM_A2A_CONFIG: GraphConfig = {
  title: "SLIM A2A Coffee Agent Communication",
  nodes: [
    {
      id: "1",
      type: "customNode",
      data: {
        icon: (
          <Box
            component="img"
            src={supervisorIcon}
            alt="Supervisor Icon"
            sx={assetPngIconBareSx(assetPngIconMonochromeDarkFilterSx())}
          />
        ),
        label1: "Supervisor Agent",
        label2: "Buyer",
        handles: "source",
        verificationStatus: "verified",
        slug: "exchange-supervisor-agent",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/corto/exchange/graph/graph.py#L22",
      },
      position: { x: 529.1332569384248, y: 159.4805787605829 },
    },
    {
      id: "2",
      type: "customNode",
      data: {
        icon: GraderAgentIcon,
        label1: "Grader Agent",
        label2: "Sommelier",
        handles: "target",
        slug: "flavor-profile-farm-agent",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/corto/farm/agent.py#L21",
      },
      position: { x: 534.0903941835277, y: 582.9317472571444 },
    },
  ],
  edges: [
    {
      id: "1-2",
      source: "1",
      target: "2",
      data: {
        label: "A2A: SLIM",
      },
      type: "custom",
    },
  ],
  animationSequence: [{ ids: ["1"] }, { ids: ["1-2"] }, { ids: ["2"] }],
}

export const graphConfig = SLIM_A2A_CONFIG

export const updateA2ALabels = async (
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void,
): Promise<void> => {
  setEdges((edges: Edge[]) =>
    edges.map((edge: Edge) =>
      edge.id === "1-2"
        ? { ...edge, data: { ...edge.data, label: "A2A: SLIM" } }
        : edge,
    ),
  )
}
