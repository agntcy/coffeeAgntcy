/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useCallback } from "react"
import type { Node, Edge } from "@xyflow/react"
import {
  PUBLISH_SUBSCRIBE_CONFIG,
  GROUP_COMMUNICATION_CONFIG,
} from "@/utils/graphConfigs"
import { EDGE_LABELS, HANDLE_TYPES } from "@/utils/const.ts"
import { logger } from "@/utils/logger"
import { AgentRecord, DiscoveryResponseEvent } from "@/types/agent"
import type { CustomNodeData } from "./Graph/Elements/types"

const DISCOVERY_KEYWORDS = [
  "brazil",
  "vietnam",
  "colombia",
  "shipper",
  "tatooine",
  "accountant",
] as const
type DiscoveryKeyword = (typeof DISCOVERY_KEYWORDS)[number]

const RECRUITER_NODE_ID = "recruiter-agent"
const RECRUITER_POS = { x: 400, y: 300 }
const NODE_WIDTH = 193
const START_Y_OFFSET = 450
const HORIZONTAL_GAP = 40

const hasKeyword = (name: string, kw: string) =>
  new RegExp(`\\b${kw}\\b`, "i").test(name)
const safeIdPart = (s: string) => s.replace(/[^a-zA-Z0-9_-]/g, "_")

const TEMPLATES_BY_KEYWORD: Record<DiscoveryKeyword, Node | undefined> = {
  brazil: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("brazil"),
  ),
  vietnam: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("vietnam"),
  ),
  colombia: PUBLISH_SUBSCRIBE_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("colombia"),
  ),
  shipper: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("shipper"),
  ),
  tatooine: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("tatooine"),
  ),
  accountant: GROUP_COMMUNICATION_CONFIG.nodes.find((n) =>
    String(n.data?.label1 ?? "")
      .toLowerCase()
      .includes("accountant"),
  ),
}

export interface UseMainAreaDiscoveryGraphParams {
  pattern: string
  discoveryResponseEvent: DiscoveryResponseEvent | null | undefined
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
  handleOpenIdentityModal: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
    nodeName?: string,
    data?: CustomNodeData,
    isMcpServer?: boolean,
  ) => void
  handleOpenOasfModal: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
  ) => void
}

/** Syncs discovery response events to the graph: adds/removes discovery nodes and edges. */
export function useMainAreaDiscoveryGraph({
  pattern,
  discoveryResponseEvent,
  setNodes,
  setEdges,
  handleOpenIdentityModal,
  handleOpenOasfModal,
}: UseMainAreaDiscoveryGraphParams) {
  const seqRef = useRef(0)
  const lastTsRef = useRef<number | null>(null)

  const addDiscoveryResponseGraph = useCallback(
    (_evt: DiscoveryResponseEvent) => {
      logger.debug("Adding discovery response graph for event", _evt)
      const raw = (_evt as { agent_records?: Record<string, AgentRecord> })
        ?.agent_records
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) return

      const entries = Object.entries(raw)
        .map(([id, rec]) => ({
          id: String(id),
          name: String(rec?.name ?? "").trim(),
          record: rec,
        }))
        .filter((e) => e.name.length > 0)

      if (entries.length === 0) {
        setNodes((prevNodes) =>
          prevNodes.filter((n) => !n.id.startsWith("discovery-")),
        )
        setEdges((prevEdges) =>
          prevEdges.filter((e) => !e.id.startsWith("edge-recruiter-agent-")),
        )
        return
      }

      const baseId = ++seqRef.current
      const templateNodeId = (kind: DiscoveryKeyword) =>
        `discovery-${kind}-${baseId}`
      const generatedNodeId = (agentId: string) =>
        `discovery-agent-${baseId}-${safeIdPart(agentId)}`
      const edgeId = (targetId: string) =>
        `edge-${RECRUITER_NODE_ID}-${baseId}-${targetId}`

      setNodes((prevNodes) => {
        const existingIds = new Set(prevNodes.map((n) => n.id))
        const existingNames = new Set(
          prevNodes
            .map((n) =>
              String((n.data as Record<string, unknown>)?.label1 ?? "")
                .trim()
                .toLowerCase(),
            )
            .filter(Boolean),
        )
        const existingCids = new Set(
          prevNodes
            .map((n) => (n.data as Record<string, unknown>)?.agentCid)
            .filter(Boolean),
        )
        const recruiterNode = prevNodes.find((n) => n.id === RECRUITER_NODE_ID)
        const recruiterIcons = recruiterNode?.data
          ? {
              icon: recruiterNode.data.icon,
              iconUrl: recruiterNode.data.iconUrl,
              image: recruiterNode.data.image,
            }
          : {}
        const templateKeywordsToAdd: DiscoveryKeyword[] =
          DISCOVERY_KEYWORDS.filter((kw) =>
            entries.some((e) => hasKeyword(e.name, kw)),
          ).filter((kw) => {
            const alreadyExists = prevNodes.some(
              (n) =>
                n.id.startsWith("discovery-") &&
                hasKeyword(
                  String((n.data as Record<string, unknown>)?.label1 ?? ""),
                  kw,
                ),
            )
            return !alreadyExists
          })
        const generatedEntriesToAdd = (() => {
          const seen = new Set<string>()
          return entries.filter((e) => {
            if (DISCOVERY_KEYWORDS.some((kw) => hasKeyword(e.name, kw)))
              return false
            const key = e.name.toLowerCase()
            if (existingNames.has(key)) return false
            if (seen.has(key)) return false
            if (existingCids.has(e.id)) return false
            seen.add(key)
            return true
          })
        })()
        const total =
          templateKeywordsToAdd.length + generatedEntriesToAdd.length
        const startCol = -Math.floor(total / 2)
        let col = 0
        const newNodes: Node[] = []
        const newEdges: Edge[] = []

        for (const kind of templateKeywordsToAdd) {
          const template = TEMPLATES_BY_KEYWORD[kind]
          if (!template) continue
          const id = templateNodeId(kind)
          if (existingIds.has(id)) continue
          const matchedEntry = entries.find((e) => hasKeyword(e.name, kind))
          if (matchedEntry?.id && existingCids.has(matchedEntry.id)) continue
          const x =
            RECRUITER_POS.x + (startCol + col) * (NODE_WIDTH + HORIZONTAL_GAP)
          const y = RECRUITER_POS.y + START_Y_OFFSET
          col++
          const { parentId, extent, ...rest } = template
          newNodes.push({
            ...rest,
            id,
            position: { x, y },
            ...(parentId && existingIds.has(parentId)
              ? { parentId, extent }
              : {}),
            data: {
              ...(template.data ?? {}),
              active: false,
              selected: false,
              agentCid: matchedEntry?.id,
              isModalOpen: false,
              onOpenIdentityModal: handleOpenIdentityModal,
              onOpenOasfModal: handleOpenOasfModal,
            },
          })
          newEdges.push({
            id: edgeId(id),
            source: RECRUITER_NODE_ID,
            target: id,
            type: "custom",
            data: { label: EDGE_LABELS.A2A_OVER_HTTP },
          })
        }

        for (const entry of generatedEntriesToAdd) {
          const id = generatedNodeId(entry.id)
          if (existingIds.has(id)) continue
          const x =
            RECRUITER_POS.x + (startCol + col) * (NODE_WIDTH + HORIZONTAL_GAP)
          const y = RECRUITER_POS.y + START_Y_OFFSET
          col++
          newNodes.push({
            id,
            type: "customNode",
            position: { x, y },
            data: {
              label1: entry.name,
              ...recruiterIcons,
              active: false,
              selected: false,
              agentCid: entry.id,
              isModalOpen: false,
              handles: HANDLE_TYPES.TARGET,
              agentDirectoryLink: "place-holder",
              oasfRecord: entry.record,
              onOpenIdentityModal: handleOpenIdentityModal,
              onOpenOasfModal: handleOpenOasfModal,
            },
          })
          newEdges.push({
            id: edgeId(id),
            source: RECRUITER_NODE_ID,
            target: id,
            type: "custom",
            data: { label: EDGE_LABELS.A2A_OVER_HTTP },
          })
        }

        if (newNodes.length === 0) return prevNodes
        setEdges((prevEdges) => {
          const existingEdgeIds = new Set(prevEdges.map((e) => e.id))
          const filtered = newEdges.filter((e) => !existingEdgeIds.has(e.id))
          return filtered.length ? [...prevEdges, ...filtered] : prevEdges
        })
        return [...prevNodes, ...newNodes]
      })
    },
    [setNodes, setEdges, handleOpenIdentityModal, handleOpenOasfModal],
  )

  useEffect(() => {
    if (pattern !== "on_demand_discovery") return
    if (!discoveryResponseEvent) return
    if (lastTsRef.current === discoveryResponseEvent.ts) return
    lastTsRef.current = discoveryResponseEvent.ts
    if (!discoveryResponseEvent.response?.trim()) return
    addDiscoveryResponseGraph(discoveryResponseEvent)
  }, [pattern, discoveryResponseEvent, addDiscoveryResponseGraph])
}
