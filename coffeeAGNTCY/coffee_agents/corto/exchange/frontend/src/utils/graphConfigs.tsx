/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import supervisorIcon from "@/assets/supervisor.png"
import graderIcon from "@/assets/Grader-Agent.png"
import { logger } from "./logger"

interface GraphConfig {
  title: string
  nodes: any[]
  edges: any[]
  animationSequence: { ids: string[] }[]
}

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  (import.meta.env as any).VITE_EXCHANGE_APP_API_URL ||
  DEFAULT_EXCHANGE_APP_API_URL

const GraderAgentIcon = (
  <img
    src={graderIcon}
    alt="Grader Agent Icon"
    style={{
      width: "16px",
      height: "16px",
      filter: "brightness(0) invert(1)",
      objectFit: "contain",
      opacity: 1,
    }}
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
              filter: "brightness(0) invert(1)",
              objectFit: "contain",
            }}
          />
        ),
        label1: "Supervisor Agent",
        label2: "Buyer",
        handles: "source",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/exchange",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
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
          "https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/farm",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
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
        label: "A2A: ",
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
  try {
    const response = await fetch(`${EXCHANGE_APP_API_URL}/transport/config`)

    const data = await response.json()
    const transport = data.transport

    setEdges((edges: any[]) =>
      edges.map((edge: any) =>
        edge.id === "1-2"
          ? { ...edge, data: { ...edge.data, label: `A2A: ${transport}` } }
          : edge,
      ),
    )
  } catch (error) {
    logger.apiError("/api/config", error)
  }
}
