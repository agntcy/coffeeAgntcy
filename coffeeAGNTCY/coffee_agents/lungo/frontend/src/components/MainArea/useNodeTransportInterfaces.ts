/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, type Dispatch, type SetStateAction } from "react"
import type { Node } from "@xyflow/react"
import { fetchOasfRecord } from "./Graph/Directory/DirectoryApi"
import { getOasfSlugFromNodeData } from "@/utils/agenticTopologyIdentityUiMap"
import { customNodeDataFromNode } from "./Graph/Elements/customNodeData"
import type { CustomNodeData } from "./Graph/Elements/types"
import {
  extractA2aTransportsFromOasf,
  type AgentTransport,
} from "./Graph/Elements/transportMeta"
import { NODE_TYPES } from "@/utils/const"
import type { ChatApiTarget } from "@/utils/patternUtils"

function readNodeData(node: Node): CustomNodeData | null {
  if (node.type !== NODE_TYPES.CUSTOM) return null
  const data = customNodeDataFromNode(node)
  if (!data?.label?.trim()) return null
  return data
}

function transportCacheKey(
  pattern: string,
  chatApiTarget: ChatApiTarget | null,
  slug: string,
): string {
  return `${pattern}\0${chatApiTarget ?? "exchange"}\0${slug}`
}

export function useNodeTransportInterfaces(
  pattern: string,
  chatApiTarget: ChatApiTarget | null,
  nodes: Node[],
  setNodes: Dispatch<SetStateAction<Node[]>>,
) {
  const inFlightKeysRef = useRef<Set<string>>(new Set())
  const transportCacheRef = useRef<Map<string, AgentTransport[]>>(new Map())
  const patternRef = useRef(pattern)
  patternRef.current = pattern
  const chatApiTargetRef = useRef(chatApiTarget)
  chatApiTargetRef.current = chatApiTarget

  useEffect(() => {
    inFlightKeysRef.current.clear()
    transportCacheRef.current.clear()
  }, [pattern, chatApiTarget])

  useEffect(() => {
    const candidates = new Map<string, CustomNodeData>()
    let hasCachedUpdates = false

    for (const node of nodes) {
      const data = readNodeData(node)
      if (!data || data.transportInterfaces !== undefined) continue

      try {
        const slug = getOasfSlugFromNodeData(data)
        const key = transportCacheKey(pattern, chatApiTarget, slug)
        if (transportCacheRef.current.has(key)) {
          hasCachedUpdates = true
          continue
        }
        if (!inFlightKeysRef.current.has(key)) {
          candidates.set(slug, data)
        }
      } catch {
        // Nodes without an OASF slug simply do not render a transport rail.
      }
    }

    if (hasCachedUpdates) {
      setNodes((prevNodes) =>
        prevNodes.map((node) => {
          const data = readNodeData(node)
          if (!data || data.transportInterfaces !== undefined) return node

          try {
            const slug = getOasfSlugFromNodeData(data)
            const cached = transportCacheRef.current.get(
              transportCacheKey(pattern, chatApiTarget, slug),
            )
            if (cached === undefined) return node
            return {
              ...node,
              data: {
                ...node.data,
                transportInterfaces: cached,
              },
            }
          } catch {
            return node
          }
        }),
      )
    }

    if (candidates.size === 0) return

    for (const [slug, nodeData] of candidates) {
      const key = transportCacheKey(pattern, chatApiTarget, slug)
      inFlightKeysRef.current.add(key)

      void fetchOasfRecord(nodeData, chatApiTarget)
        .then((record) => extractA2aTransportsFromOasf(record))
        .catch(() => [] as AgentTransport[])
        .then((transportInterfaces) => {
          inFlightKeysRef.current.delete(key)
          if (
            patternRef.current !== pattern ||
            chatApiTargetRef.current !== chatApiTarget
          ) {
            return
          }

          transportCacheRef.current.set(key, transportInterfaces)
          setNodes((prevNodes) =>
            prevNodes.map((node) => {
              const data = readNodeData(node)
              if (!data || data.transportInterfaces !== undefined) return node

              try {
                if (getOasfSlugFromNodeData(data) !== slug) return node
              } catch {
                return node
              }

              return {
                ...node,
                data: {
                  ...node.data,
                  transportInterfaces,
                },
              }
            }),
          )
        })
    }
  }, [pattern, chatApiTarget, nodes, setNodes])
}
