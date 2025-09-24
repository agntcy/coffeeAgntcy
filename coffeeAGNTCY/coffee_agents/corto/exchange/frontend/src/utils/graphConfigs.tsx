/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Node, Edge } from "@xyflow/react"
import supervisorIcon from "@/assets/supervisor.png"
import graderIcon from "@/assets/Grader-Agent.png"

export interface GraphConfig {
  title: string
  nodes: Node[]
  edges: Edge[]
  animationSequence: { ids: string[] }[]
}

const GraderAgentIcon = (
  <img
    src={graderIcon}
    alt="Grader Agent Icon"
    style={{
      width: "16px",
      height: "16px",
      objectFit: "contain",
      opacity: 1,
    }}
    className="dark-icon"
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
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            style={{
              width: "16px",
              height: "16px",
              objectFit: "contain",
            }}
            className="dark-icon"
          />
        ),
        label1: "Supervisor Agent",
        label2: "Buyer",
        handles: "source",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/corto/exchange/graph/graph.py#L22",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/a4940cac-fbf1-40a7-bf11-d5c67e7e0b82",
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
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/corto/farm/agent.py#L21",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/0bd11abc-2148-402e-abc2-568cce55117c",
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
  setEdges: (updater: (edges: any[]) => any[]) => void,
): Promise<void> => {
  setEdges((edges: any[]) =>
    edges.map((edge: any) =>
      edge.id === "1-2"
        ? { ...edge, data: { ...edge.data, label: "A2A: SLIM" } }
        : edge,
    ),
  )
}
