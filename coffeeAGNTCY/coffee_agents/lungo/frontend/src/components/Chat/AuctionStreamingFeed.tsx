/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import { Loader2 } from "lucide-react"
import AgentIcon from "@/assets/Coffee_Icon.svg"
import CheckCircle from "@/assets/Check_Circle.png"
import { AuctionStreamingFeedProps } from "@/types/streaming"

const AuctionStreamingFeed: React.FC<AuctionStreamingFeedProps> = ({
  isVisible,
  onComplete,
  prompt,
  onStreamComplete,
  auctionStreamingState,
  apiError,
}) => {
  const isComplete = auctionStreamingState?.status === "completed"

  useEffect(() => {
    if (isComplete && auctionStreamingState?.events.length > 0) {
      if (onComplete) {
        onComplete()
      }

      if (onStreamComplete) {
        onStreamComplete()
      }
    }
  }, [
    isComplete,
    auctionStreamingState?.events.length,
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
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-bold leading-5 text-chat-text">
            Streaming output:
          </div>
        ) : prompt && !apiError ? (
          <div className="whitespace-pre-wrap break-words font-cisco text-sm font-bold leading-5 text-chat-text">
            Streaming<span className="loading-dots ml-1"></span>
          </div>
        ) : null}

        {prompt && !isComplete && !apiError && events.length === 0 && (
          <div className="mt-3 flex w-full flex-row items-start gap-1">
            <div className="mt-1 flex items-center">
              <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />
            </div>
            <div className="flex-1"></div>
          </div>
        )}

        <div className="mt-3 flex w-full flex-col items-start gap-3">
          {events.map((event, index) => {
            const isLastEvent = isComplete && index === events.length - 1
            const label = isLastEvent
              ? "Final response:"
              : `Response ${index + 1}:`

            return (
              <div
                key={`auction-${index}`}
                className="flex w-full flex-row items-start gap-1"
              >
                <div className="mt-1 flex items-center">
                  <img src={CheckCircle} alt="Complete" className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="font-inter text-sm leading-[18px] text-chat-text">
                    <span className="font-bold">{label}</span> {event.response}
                  </div>
                </div>
              </div>
            )
          })}

          {events.length > 0 && !isComplete && (
            <div className="flex w-full flex-row items-start gap-1">
              <div className="mt-1 flex items-center">
                <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />
              </div>
              <div className="flex-1"></div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AuctionStreamingFeed
