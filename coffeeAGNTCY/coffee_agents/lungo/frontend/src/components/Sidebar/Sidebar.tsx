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
  const [isTransportExpanded, setIsTransportExpanded] = useState(true)
  const [transport, setTransport] = useState<string>("")

  const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
  const EXCHANGE_APP_API_URL =
    (import.meta.env as any).VITE_EXCHANGE_APP_API_URL ||
    DEFAULT_EXCHANGE_APP_API_URL

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

  const handleTransportToggle = () => {
    setIsTransportExpanded(!isTransportExpanded)
  }

  return (
    <div className="flex h-full w-[320px] flex-col items-start gap-5 border-r border-[#0D274D] bg-sidebar-background px-4 py-0 font-inter">
      <div className="mt-5 flex w-[288px] flex-col items-start gap-0 p-0">
        <div className="flex w-[288px] flex-col items-start p-0">
          <div className="flex h-9 w-[288px] items-start gap-2 bg-sidebar-background p-2 transition-colors hover:bg-[#373C42]">
            <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white">
              Conversation: Coffee Buying
            </span>
          </div>

          <div className="flex w-[288px] flex-col items-start gap-0 p-0">
            <div className="flex h-9 w-[288px] items-start gap-2 bg-sidebar-background px-5 py-2 transition-colors hover:bg-[#373C42]">
              <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white">
                Agentic Patterns
              </span>
            </div>

            <div>
              <SidebarDropdown
                title="Publish Subscribe "
                isExpanded={isTransportExpanded}
                onToggle={handleTransportToggle}
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
      </div>
    </div>
  )
}

export default Sidebar
