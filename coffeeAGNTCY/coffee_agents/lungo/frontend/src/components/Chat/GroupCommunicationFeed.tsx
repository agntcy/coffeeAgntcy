/**

 * Copyright AGNTCY Contributors (https://github.com/agntcy)

 * SPDX-License-Identifier: Apache-2.0

 **/

import React, { useState, useEffect, useCallback, useMemo } from "react"

import { ChevronDown, ChevronUp, Truck, Calculator } from "lucide-react"

import AgentIcon from "@/assets/Coffee_Icon.svg"

import supervisorIcon from "@/assets/supervisor.png"

import farmAgentIcon from "@/assets/Grader-Agent.png"

interface StreamStep {
  order_id: string

  sender: string

  receiver: string

  message: string

  timestamp: string

  state: string

  final?: boolean
}

interface GroupCommunicationFeedProps {
  isVisible: boolean
  onComplete?: () => void
  prompt: string
  onStreamComplete?: () => void
  onSenderHighlight?: (nodeId: string) => void
  graphConfig?: any
  sseState?: {
    isConnected: boolean
    isConnecting: boolean
    events: StreamStep[]
    currentOrderId: string | null
    error: string | null
    clearEvents: () => void
  }
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
  onComplete,
  prompt,
  onSenderHighlight,
  graphConfig,
  sseState,
}) => {
  const [state, setState] = useState({
    isExpanded: true,
    isComplete: false,
  })

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

  const handleSenderHighlight = useCallback(
    (streamData: StreamStep) => {
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
    },
    [onSenderHighlight, graphConfig],
  )

  const handleExpand = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: true }))
  }, [])

  const handleCollapse = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: false }))
  }, [])

  // Reset state when a new prompt comes in (new request started)
  useEffect(() => {
    if (prompt) {
      setState((prev) => ({
        ...prev,
        isComplete: false,
        isExpanded: true,
      }))
    }
  }, [prompt])

  useEffect(() => {
    if (!sseState?.events.length) return

    const lastEvent = sseState.events[sseState.events.length - 1]

    handleSenderHighlight(lastEvent)

    const isFinalStep =
      lastEvent.final === true || lastEvent.state === "DELIVERED"

    if (isFinalStep && !state.isComplete) {
      setState((prev) => ({
        ...prev,
        isComplete: true,
      }))

      setTimeout(() => {
        setState((prev) => ({
          ...prev,
          isExpanded: false,
        }))
      }, 2000)

      if (onComplete) {
        onComplete()
      }
    }
  }, [sseState?.events, handleSenderHighlight, state.isComplete, onComplete])

  if (!isVisible) {
    return null
  }

  const events = sseState?.events || []
  const isConnecting = sseState?.isConnecting || false
  const hasError = sseState?.error || null

  // Don't render anything if there's no prompt and no events
  if (!prompt && events.length === 0) {
    return null
  }

  return (
    <div className="flex w-full flex-row items-start gap-1 transition-all duration-300">
      <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
        <img src={AgentIcon} alt="Agent" className="h-[22px] w-[22px]" />
      </div>

      <div className="flex max-w-[calc(100%-3rem)] flex-1 flex-col items-start rounded p-1 px-2">
        {/* Show status messages */}
        {hasError ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Connection error: {hasError}
          </div>
        ) : isConnecting ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Connecting to agent stream...
          </div>
        ) : state.isComplete ? (
          // Show completion message only when done and collapsed
          state.isExpanded ? null : (
            <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
              {prompt || "Request Processed"}
            </div>
          )
        ) : prompt && events.length === 0 ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Processing Request...
          </div>
        ) : null}

        {/* Show completion message only when done */}
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

        {/* Always show events when expanded or when events exist */}
        {(state.isExpanded || events.length > 0) && (
          <>
            <div className="flex w-full flex-col items-start gap-2">
              {events.map((step, index) => (
                <div
                  key={`${step.order_id}-${index}`}
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
