/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { PatternType, PATTERNS } from "@/App"
import SidebarItem from "./sidebarItem"
import SidebarDropdown from "./SidebarDropdown"

interface SidebarProps {
  selectedPattern: PatternType
  onPatternChange: (pattern: PatternType) => void
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedPattern,
  onPatternChange,
}) => {
  const [isPublishSubscribeExpanded, setIsPublishSubscribeExpanded] =
    useState(true)
  const [isGroupCommunicationExpanded, setIsGroupCommunicationExpanded] =
    useState(true)
  const [transport, setTransport] = useState<string>("")

  const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
  const EXCHANGE_APP_API_URL =
    import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL

  useEffect(() => {
    const fetchTransportConfig = async () => {
      try {
        const response = await fetch(`${EXCHANGE_APP_API_URL}/transport/config`)
        const data = await response.json()
        if (data.transport) {
          setTransport(data.transport)
        }
      } catch (error) {
        console.error("Error fetching transport config:", error)
      }
    }

    fetchTransportConfig()
  }, [EXCHANGE_APP_API_URL])

  const handlePublishSubscribeToggle = () => {
    setIsPublishSubscribeExpanded(!isPublishSubscribeExpanded)
  }

  const handleGroupCommunicationToggle = () => {
    setIsGroupCommunicationExpanded(!isGroupCommunicationExpanded)
  }

  return (
    <div className="flex h-full w-64 flex-none flex-col gap-5 border-r border-sidebar-border bg-sidebar-background font-inter lg:w-[320px]">
      <div className="flex h-full flex-1 flex-col gap-5 p-4">
        <div className="flex flex-col">
          <div className="flex min-h-[36px] w-full items-center gap-2 rounded py-2 pl-2 pr-5">
            <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
              Conversation: Coffee Buying
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex min-h-[36px] w-full items-center gap-2 rounded py-2 pl-5 pr-5">
              <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
                Agentic Patterns
              </span>
            </div>

            <div>
              <SidebarDropdown
                title="Publish Subscribe "
                isExpanded={isPublishSubscribeExpanded}
                onToggle={handlePublishSubscribeToggle}
              >
                <SidebarItem
                  title={`A2A ${transport}`}
                  isSelected={selectedPattern === PATTERNS.PUBLISH_SUBSCRIBE}
                  onClick={() => onPatternChange(PATTERNS.PUBLISH_SUBSCRIBE)}
                />
              </SidebarDropdown>
            </div>
          </div>
        </div>

        <div className="flex flex-col">
          <div className="flex min-h-[36px] w-full items-center gap-2 rounded py-2 pl-2 pr-5">
            <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
              Conversation: Order Fulfilment
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex min-h-[36px] w-full items-center gap-2 rounded py-2 pl-5 pr-5">
              <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text">
                Agentic Patterns
              </span>
            </div>

            <div>
              <SidebarDropdown
                title="Secure Group Communication"
                isExpanded={isGroupCommunicationExpanded}
                onToggle={handleGroupCommunicationToggle}
              >
                <SidebarItem
                  title="A2A SLIM"
                  isSelected={selectedPattern === PATTERNS.GROUP_COMMUNICATION}
                  onClick={() => onPatternChange(PATTERNS.GROUP_COMMUNICATION)}
                />
              </SidebarDropdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
