/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, type Dispatch, type SetStateAction } from "react"
import type { Node } from "@xyflow/react"
import {
  fetchOasfRecord,
  getOasfSlugFromNodeData,
} from "./Graph/Directory/DirectoryApi"
import { customNodeDataFromNode } from "./Graph/Elements/customNodeData"
import type { CustomNodeData } from "./Graph/Elements/types"
import {
  extractA2aTransportsFromOasf,
  type AgentTransport,
} from "./Graph/Elements/transportMeta"
import { NODE_TYPES } from "@/utils/const"

function readNodeData(node: Node): CustomNodeData | null {
  if (node.type !== NODE_TYPES.CUSTOM) return null
  const data = customNodeDataFromNode(node)
  if (!data?.label?.trim()) return null
  return data
}

export function useNodeTransportInterfaces(
  pattern: string,
  nodes: Node[],
  setNodes: Dispatch<SetStateAction<Node[]>>,
) {
  const inFlightKeysRef = useRef<Set<string>>(new Set())
  const transportCacheRef = useRef<Map<string, AgentTransport[]>>(new Map())
  const patternRef = useRef(pattern)
  patternRef.current = pattern

  useEffect(() => {
    inFlightKeysRef.current.clear()
    transportCacheRef.current.clear()
  }, [pattern])

  useEffect(() => {
    const candidates = new Map<string, CustomNodeData>()
    let hasCachedUpdates = false

    for (const node of nodes) {
      const data = readNodeData(node)
      if (!data || data.transportInterfaces !== undefined) continue

      try {
        const slug = getOasfSlugFromNodeData(data)
        const key = `${pattern}\0${slug}`
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
            const cached = transportCacheRef.current.get(`${pattern}\0${slug}`)
            if (!cached) return node
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
      const key = `${pattern}\0${slug}`
      inFlightKeysRef.current.add(key)

      void fetchOasfRecord(nodeData)
        .then((record) => extractA2aTransportsFromOasf(record))
        .catch(() => [])
        .then((transportInterfaces) => {
          inFlightKeysRef.current.delete(key)
          if (patternRef.current !== pattern) return
          if (transportInterfaces.length === 0) return

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
  }, [pattern, nodes, setNodes])
}
