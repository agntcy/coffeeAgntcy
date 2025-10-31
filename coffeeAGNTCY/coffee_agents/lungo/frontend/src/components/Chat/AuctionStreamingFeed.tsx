/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback, useRef } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/CheckCircle.png"
import { AuctionStreamingFeedProps } from "@/types/streaming"

const AuctionStreamingFeed: React.FC<AuctionStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  sseState,
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
    if (!sseState?.events.length) return

    const hasMultipleResponses = sseState.events.length >= 3

    if (hasMultipleResponses && !state.isComplete) {
      setState((prev) => ({
        ...prev,
        isComplete: true,
      }))

      if (onComplete) {
        onComplete()
      }

      if (onStreamComplete) {
        onStreamComplete()
      }
    }
  }, [sseState?.events, state.isComplete, onComplete, onStreamComplete])

  if (!isVisible) {
    return null
  }

  const events = sseState?.events || []
  const errorMessage = sseState?.error || null

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
        ) : state.isComplete ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Auction streaming completed
          </div>
        ) : prompt && !apiError ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-normal leading-5 text-chat-text">
            Streaming auction data...
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
                View Auction Details
              </span>
            </div>
          </div>
        )}

        {state.isExpanded && (
          <>
            <div className="mt-3 flex w-full flex-col items-start gap-3">
              {events.map((event, index) => {
                return (
                  <div
                    key={`auction-${index}`}
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
                        <span className="font-normal">{event.response}</span>
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

export default AuctionStreamingFeed
