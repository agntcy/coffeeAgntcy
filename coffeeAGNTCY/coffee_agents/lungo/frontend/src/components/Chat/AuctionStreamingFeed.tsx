/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/CheckCircle.png"
import { AuctionStreamingFeedProps } from "@/types/streaming"

const AuctionStreamingFeed: React.FC<AuctionStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  auctionStreamingState,
  executionKey,
  apiError,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true)
  const [isComplete, setIsComplete] = useState<boolean>(false)

  const handleExpand = useCallback(() => {
    setIsExpanded(true)
  }, [])

  const handleCollapse = useCallback(() => {
    setIsExpanded(false)
  }, [])

  useEffect(() => {
    if (prompt) {
      setIsComplete(false)
      setIsExpanded(true)
    }
  }, [prompt])

  useEffect(() => {
    if (
      auctionStreamingState?.events.length === 0 &&
      auctionStreamingState?.isConnecting
    ) {
      setIsComplete(false)
      setIsExpanded(true)
    }
  }, [
    auctionStreamingState?.events.length,
    auctionStreamingState?.isConnecting,
  ])

  useEffect(() => {
    if (executionKey) {
      setIsComplete(false)
      setIsExpanded(true)
    }
  }, [executionKey])

  useEffect(() => {
    if (!auctionStreamingState?.events.length) return

    const isStreamingComplete =
      auctionStreamingState.events.length > 0 &&
      !auctionStreamingState.isConnecting &&
      !auctionStreamingState.isConnected

    if (isStreamingComplete && !isComplete) {
      setIsComplete(true)

      if (onComplete) {
        onComplete()
      }

      if (onStreamComplete) {
        onStreamComplete()
      }
    }
  }, [
    auctionStreamingState?.events,
    auctionStreamingState?.isConnecting,
    auctionStreamingState?.isConnected,
    isComplete,
    onComplete,
    onStreamComplete,
  ])

  if (!isVisible) {
    return null
  }

  const events = auctionStreamingState?.events || []
  const errorMessage = auctionStreamingState?.error || null

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
        ) : isComplete ? (
          <div className="flex items-center gap-2 whitespace-pre-wrap break-words font-cisco text-sm font-medium leading-5">
            <div className="h-2 w-2 rounded-full bg-green-700" />
            <span className="text-green-700">Complete</span>
          </div>
        ) : prompt && !apiError ? (
          <div className="flex items-center gap-2 whitespace-pre-wrap break-words font-cisco text-sm font-medium leading-5">
            <div className="h-2 w-2 animate-pulse rounded-full bg-gray-400" />
            <span className="text-chat-text">Streaming...</span>
          </div>
        ) : null}

        {prompt && !isComplete && !apiError && events.length === 0 && (
          <div className="mt-3 flex w-full flex-row items-start gap-1">
            <div className="mt-1 flex items-center">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-b-transparent border-l-transparent border-r-accent-primary border-t-accent-primary" />
            </div>
            <div className="flex-1"></div>
          </div>
        )}

        {isComplete && !isExpanded && (
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

        {isExpanded && (
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
                      <span className="font-inter text-sm leading-[18px] text-chat-text">
                        <span className="font-normal">{event.response}</span>
                      </span>
                    </div>
                  </div>
                )
              })}

              {events.length > 0 && !isComplete && (
                <div className="flex w-full flex-row items-start gap-1">
                  <div className="mt-1 flex items-center">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-b-transparent border-l-transparent border-r-accent-primary border-t-accent-primary" />
                  </div>
                  <div className="flex-1"></div>
                </div>
              )}
            </div>

            {isComplete && (
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
