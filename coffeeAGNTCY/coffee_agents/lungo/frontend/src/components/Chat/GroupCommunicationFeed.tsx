/**

 * Copyright AGNTCY Contributors (https://github.com/agntcy)

 * SPDX-License-Identifier: Apache-2.0

 **/

import React, { useState, useEffect, useCallback, useRef } from "react"

import { ChevronDown, ChevronUp } from "lucide-react"

import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/CheckCircle.png"
import {
  GroupCommunicationFeedProps,
  LogisticsStreamStep,
} from "@/types/streaming"

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

      if (node.data.label1 === "Buyer") {
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

const formatAgentName = (agentName: string): string => {
  if (agentName === "Supervisor") {
    return "Buyer"
  }
  if (agentName === "Tatooine Farm") {
    return "Tatooine"
  }

  return agentName
}

const GroupCommunicationFeed: React.FC<GroupCommunicationFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onSenderHighlight,
  graphConfig,
  streamingState,
  executionKey,
  apiError,
}) => {
  const [state, setState] = useState({
    isExpanded: true,
    isComplete: false,
  })

  const lastProcessedEventRef = useRef<string | null>(null)
  const highlightTimeoutsRef = useRef<number[]>([])

  const handleExpand = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: true }))
  }, [])

  const handleCollapse = useCallback(() => {
    setState((prev) => ({ ...prev, isExpanded: false }))
  }, [])

  useEffect(() => {
    if (prompt) {
      highlightTimeoutsRef.current.forEach(clearTimeout)
      highlightTimeoutsRef.current = []

      setState((prev) => ({
        ...prev,
        isComplete: false,
        isExpanded: true,
      }))
      lastProcessedEventRef.current = null
    }
  }, [prompt])

  useEffect(() => {
    if (executionKey) {
      highlightTimeoutsRef.current.forEach(clearTimeout)
      highlightTimeoutsRef.current = []

      setState({
        isComplete: false,
        isExpanded: true,
      })
      lastProcessedEventRef.current = null
    }
  }, [executionKey])

  useEffect(() => {
    return () => {
      highlightTimeoutsRef.current.forEach(clearTimeout)
    }
  }, [])

  useEffect(() => {
    if (!streamingState?.events.length) return

    const lastEvent = streamingState.events[streamingState.events.length - 1]
    const eventKey = `${lastEvent.order_id}-${lastEvent.timestamp}-${lastEvent.sender}-${lastEvent.receiver}`

    if (lastProcessedEventRef.current === eventKey) {
      return
    }

    lastProcessedEventRef.current = eventKey

    if (onSenderHighlight && lastEvent.sender && graphConfig) {
      const senderToNodeMap = buildSenderToNodeMap(graphConfig)
      const senderNodeId =
        senderToNodeMap[lastEvent.sender] ||
        senderToNodeMap[lastEvent.sender.toLowerCase()]

      if (senderNodeId) {
        onSenderHighlight(senderNodeId)

        if (lastEvent.sender === "Supervisor") {
          highlightTimeoutsRef.current.forEach(clearTimeout)
          highlightTimeoutsRef.current = []

          const allAgentIds = getAllAgentNodeIds(graphConfig)

          const highlightAgents = (nodeIds: string[], startIndex = 0) => {
            if (startIndex >= nodeIds.length) return

            const timeoutId = window.setTimeout(() => {
              onSenderHighlight(nodeIds[startIndex])
              highlightAgents(nodeIds, startIndex + 1)
            }, 100)

            highlightTimeoutsRef.current.push(timeoutId)
          }

          highlightAgents(allAgentIds)
        }
      }
    }

    const isFinalStep = lastEvent.state === "DELIVERED"

    if (isFinalStep && !state.isComplete) {
      setState((prev) => ({
        ...prev,
        isComplete: true,
      }))

      if (onComplete) {
        onComplete()
      }
    }
  }, [
    streamingState?.events,
    onSenderHighlight,
    graphConfig,
    state.isComplete,
    onComplete,
  ])

  if (!isVisible) {
    return null
  }

  const events = streamingState?.events || []
  const errorMessage = streamingState?.error || null

  if ((!prompt && events.length === 0) || apiError) {
    return null
  }

  return (
    <div className="flex w-full flex-row items-start gap-1 transition-all duration-300">
      <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
        <img src={AgentIcon} alt="Agent" className="h-[22px] w-[22px]" />
      </div>

      <div className="flex max-w-[calc(100%-3rem)] flex-1 flex-col items-start rounded p-1 px-2">
        {errorMessage ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Connection error: {errorMessage}
          </div>
        ) : state.isComplete && streamingState?.currentOrderId ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Order {streamingState.currentOrderId}
          </div>
        ) : prompt && !apiError ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Processing Request...
          </div>
        ) : null}

        {prompt && !state.isComplete && !apiError && events.length === 0 && (
          <div className="mt-3 flex w-full flex-row items-start gap-1">
            <div className="mt-1 flex items-center">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-b-transparent border-l-transparent border-r-accent-primary border-t-accent-primary" />
            </div>
            <div className="flex-1"></div>
          </div>
        )}

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
            <div className="mt-3 flex w-full flex-col items-start gap-3">
              {events.map((step: LogisticsStreamStep, index: number) => {
                return (
                  <div
                    key={`${step.order_id}-${index}`}
                    className="flex w-full flex-row items-start gap-1"
                  >
                    <div className="mt-1 flex items-center">
                      <img
                        src={CheckCircle}
                        alt="Complete"
                        className="h-4 w-4"
                      />
                    </div>

                    <div className="flex-1">
                      <span className="font-['Inter'] text-sm leading-[18px] text-chat-text">
                        <span className="font-semibold">
                          {formatAgentName(step.sender)}
                        </span>
                        {index === 0 && (
                          <>
                            → <span className="font-semibold">All Agents</span>
                          </>
                        )}
                        : <span className="font-normal">"{step.message}"</span>
                      </span>
                    </div>
                  </div>
                )
              })}

              {events.length > 0 && !state.isComplete && (
                <div className="flex w-full flex-row items-start gap-1">
                  <div className="mt-1 flex items-center">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-b-transparent border-l-transparent border-r-accent-primary border-t-accent-primary" />
                  </div>
                  <div className="flex-1"></div>
                </div>
              )}
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

export default GroupCommunicationFeed
