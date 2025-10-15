/**

 * Copyright AGNTCY Contributors (https://github.com/agntcy)

 * SPDX-License-Identifier: Apache-2.0

 **/

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"

import { ChevronDown, ChevronUp, Truck, Calculator } from "lucide-react"

import AgentIcon from "@/assets/Coffee_Icon.svg"

import supervisorIcon from "@/assets/supervisor.png"

import farmAgentIcon from "@/assets/Grader-Agent.png"

const DEFAULT_HELPDESK_API_URL = "http://127.0.0.1:9094"

const HELPDESK_API_URL =
  import.meta.env.VITE_HELPDESK_API_URL || DEFAULT_HELPDESK_API_URL

interface StreamStep {
  connection_id: string

  sender: string

  receiver: string

  message: string

  timestamp: string

  state: string

  final: boolean
}

const isValidStreamStep = (data: any): data is StreamStep => {
  if (!data || typeof data !== "object") {
    return false
  }

  const requiredStringFields = [
    "connection_id",
    "sender",
    "receiver",
    "message",
    "timestamp",
    "state",
  ]
  for (const field of requiredStringFields) {
    if (typeof data[field] !== "string" || data[field].trim() === "") {
      console.warn(`Invalid or empty ${field} in stream data:`, data[field])
      return false
    }
  }

  if (typeof data.final !== "boolean") {
    console.warn("Invalid final field in stream data:", data.final)
    return false
  }

  return true
}

interface GroupCommunicationFeedProps {
  isVisible: boolean
  shouldConnect: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: any
}

const buildSenderToNodeMap = (graphConfig: any): Record<string, string> => {
  if (!graphConfig?.nodes) return {}

  const map: Record<string, string> = {}

  graphConfig.nodes.forEach((node: any) => {
    if (node.data) {
      if (node.data.label1) {
        map[node.data.label1] = node.id
        map[node.data.label1.toLowerCase()] = node.id
      }
      if (node.data.label2) {
        map[node.data.label2] = node.id
        map[node.data.label2.toLowerCase()] = node.id
      }
      if (node.data.agentName) {
        map[node.data.agentName] = node.id
        map[node.data.agentName.toLowerCase()] = node.id
      }
      if (node.data.farmName) {
        map[node.data.farmName] = node.id
        map[node.data.farmName.toLowerCase()] = node.id
      }

      if (node.data.label1 === "Logistics Agent") {
        map["Supervisor"] = node.id
        map["supervisor"] = node.id
      }
      if (node.data.label1 === "Tatooine") {
        map["Tatooine Farm"] = node.id
        map["tatooine farm"] = node.id
      }
    }
  })

  return map
}

const getAllAgentNodeIds = (graphConfig: any): string[] => {
  if (!graphConfig?.nodes) return []

  return graphConfig.nodes
    .filter(
      (node: any) =>
        node.type === "customNode" && node.data?.label1 !== "Logistics Agent",
    )
    .map((node: any) => node.id)
}

const SENDER_ICON_MAP = {
  logistics: () => (
    <img
      src={supervisorIcon}
      alt="Logistics Icon"
      className="dark-icon h-4 w-4 object-contain opacity-100"
    />
  ),
  supervisor: () => (
    <img
      src={supervisorIcon}
      alt="Supervisor Icon"
      className="dark-icon h-4 w-4 object-contain opacity-100"
    />
  ),
  tatooine: () => (
    <img
      src={farmAgentIcon}
      alt="Farm Icon"
      className="dark-icon h-4 w-4 object-contain opacity-100"
    />
  ),
  farm: () => (
    <img
      src={farmAgentIcon}
      alt="Farm Icon"
      className="dark-icon h-4 w-4 object-contain opacity-100"
    />
  ),
  shipper: () => (
    <Truck className="dark-icon h-4 w-4 object-contain opacity-100" />
  ),
  accountant: () => (
    <Calculator className="dark-icon h-4 w-4 object-contain opacity-100" />
  ),
} as const

const getSenderIcon = (sender: string) => {
  const senderLower = sender.toLowerCase()

  const matchedKey = Object.keys(SENDER_ICON_MAP).find((key) =>
    senderLower.includes(key),
  ) as keyof typeof SENDER_ICON_MAP

  return matchedKey ? (
    SENDER_ICON_MAP[matchedKey]()
  ) : (
    <Calculator className="dark-icon h-4 w-4 object-contain opacity-100" />
  )
}

const GroupCommunicationFeed: React.FC<GroupCommunicationFeedProps> = ({
  isVisible,
  shouldConnect,
  onComplete,
  prompt,
  onSenderHighlight,
  graphConfig,
}) => {
  const [state, setState] = useState({
    steps: [] as StreamStep[],
    isExpanded: true,
    isConnecting: false,
    isComplete: false,
  })

  const sseConnectionRef = useRef<EventSource | null>(null)

  const memoizedGetSenderIcon = useMemo(() => {
    const cache = new Map<string, React.ReactNode>()

    return (sender: string) => {
      if (cache.has(sender)) {
        return cache.get(sender)!
      }

      const icon = getSenderIcon(sender)
      cache.set(sender, icon)
      return icon
    }
  }, [])

  const handleConnectionOpen = useCallback(() => {
    console.log("SSE connection opened")
    setState((prev) => ({ ...prev, isConnecting: false }))
  }, [])

  const handleStreamMessage = useCallback(
    (streamData: StreamStep) => {
      console.log("Parsed stream data:", streamData)

      if (onSenderHighlight && streamData.sender && graphConfig) {
        const senderToNodeMap = buildSenderToNodeMap(graphConfig)

        const senderNodeId =
          senderToNodeMap[streamData.sender] ||
          senderToNodeMap[streamData.sender.toLowerCase()]

        if (senderNodeId) {
          onSenderHighlight(senderNodeId)

          if (streamData.receiver === "All Agents") {
            const allAgentIds = getAllAgentNodeIds(graphConfig)

            allAgentIds.forEach((nodeId, index) => {
              setTimeout(() => onSenderHighlight(nodeId), (index + 1) * 100)
            })
          }
        }
      }

      if (streamData.final) {
        setState((prev) => ({
          ...prev,
          steps: [...prev.steps, streamData],
          isComplete: true,
        }))

        setTimeout(() => {
          setState((prev) => ({
            ...prev,
            isExpanded: false,
          }))
        }, 2000)

        if (sseConnectionRef.current) {
          sseConnectionRef.current.close()
        }

        if (onComplete) {
          onComplete()
        }
      } else {
        setState((prev) => ({
          ...prev,
          steps: [...prev.steps, streamData],
        }))
      }
    },
    [onComplete, onSenderHighlight, graphConfig],
  )

  const handleConnectionError = useCallback((error: Event) => {
    console.error("SSE connection error:", error)
    setState((prev) => ({ ...prev, isConnecting: false }))

    if (sseConnectionRef.current) {
      sseConnectionRef.current.close()
    }
  }, [])

  const handleExpand = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: true }))
  }, [])

  const handleCollapse = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: false }))
  }, [])

  useEffect(() => {
    console.log(
      "ProgressTracker useEffect triggered, shouldConnect:",
      shouldConnect,
    )

    if (!shouldConnect) {
      if (sseConnectionRef.current) {
        console.log("Closing existing EventSource due to shouldConnect=false")

        sseConnectionRef.current.close()

        sseConnectionRef.current = null
      }

      setState({
        steps: [],
        isExpanded: true,
        isConnecting: false,
        isComplete: false,
      })

      return
    }

    if (sseConnectionRef.current) {
      return
    }

    setState((prev) => ({ ...prev, isConnecting: true }))

    const eventSource = new EventSource(`${HELPDESK_API_URL}/agent/stream`)

    sseConnectionRef.current = eventSource

    eventSource.onopen = handleConnectionOpen

    eventSource.onmessage = (event) => {
      console.log("SSE message received:", event.data)

      try {
        const parsedData = JSON.parse(event.data)

        if (!isValidStreamStep(parsedData)) {
          console.error("Invalid stream data structure received:", {
            received: parsedData,
            expected:
              "StreamStep with connection_id, sender, receiver, message, timestamp, state (strings) and final (boolean)",
          })
          return
        }

        handleStreamMessage(parsedData)
      } catch (error) {
        console.error("Failed to parse SSE data as JSON:", {
          error: error,
          rawData: event.data,
        })
      }
    }

    eventSource.onerror = handleConnectionError

    return () => {
      console.log("Cleaning up EventSource connection")

      if (sseConnectionRef.current) {
        sseConnectionRef.current.close()

        sseConnectionRef.current = null
      }
    }
  }, [shouldConnect])

  if (!isVisible) {
    return null
  }

  return (
    <div className="flex w-full flex-row items-start gap-1 transition-all duration-300">
      <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
        <img src={AgentIcon} alt="Agent" className="h-[22px] w-[22px]" />
      </div>

      <div className="flex max-w-[calc(100%-3rem)] flex-1 flex-col items-start rounded p-1 px-2">
        <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
          {state.isConnecting
            ? "Connecting to agent stream..."
            : state.isComplete
              ? prompt || "Request Processed"
              : "Processing Request..."}
        </div>{" "}
        {state.isComplete && !state.isExpanded && (
          <div
            className="mt-1 flex w-full cursor-pointer flex-row items-center gap-1 hover:opacity-75"
            onClick={handleExpand}
          >
            <div className="h-4 w-4 flex-none">
              <ChevronDown className="h-4 w-4 text-chat-text" />
            </div>

            <div className="flex-1">
              <span className="font-cisco text-sm font-normal leading-[18px] text-chat-text">
                View Details
              </span>
            </div>
          </div>
        )}
        {state.isExpanded && (
          <>
            <div className="flex w-full flex-col items-start gap-2">
              {state.steps.map((step, index) => (
                <div
                  key={`${step.connection_id}-${index}`}
                  className="flex w-full flex-row items-center gap-2"
                >
                  <div className="h-4 w-4 flex-none">
                    {memoizedGetSenderIcon(step.sender)}
                  </div>

                  <div className="flex-1">
                    <span className="font-cisco text-sm font-normal leading-[18px] text-chat-text">
                      {step.sender} → {step.message}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {state.isComplete && (
              <div
                className="flex w-full cursor-pointer flex-row items-center gap-1 pt-2 hover:opacity-75"
                onClick={handleCollapse}
              >
                <div className="h-4 w-4 flex-none">
                  <ChevronUp className="h-4 w-4 text-chat-text" />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default React.memo(GroupCommunicationFeed)
