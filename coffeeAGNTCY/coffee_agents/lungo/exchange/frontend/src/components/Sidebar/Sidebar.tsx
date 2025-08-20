/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { ChevronUp } from "lucide-react"
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
  const [isBuyerExpanded, setIsBuyerExpanded] = useState(true) // Auto-expanded
  const [isTransportExpanded, setIsTransportExpanded] = useState(true)

  const handleBuyerToggle = () => {
    setIsBuyerExpanded(!isBuyerExpanded)
  }

  const handleTransportToggle = () => {
    setIsTransportExpanded(!isTransportExpanded)
  }

  return (
    <div className="order-0 bg-primary-bg box-border flex h-full w-[320px] flex-none flex-grow-0 flex-col items-start self-stretch border-r border-[#0D274D] px-0 py-4 font-inter">
      <div className="bg-primary-bg flex h-full w-[320px] flex-1 flex-col items-start gap-5 px-4 py-0">
        <div className="order-1 flex h-[524px] w-[288px] flex-none flex-grow-0 flex-col items-start self-stretch p-0 font-inter">
          <div className="order-0 flex h-[72px] w-[288px] flex-none flex-grow-0 flex-col items-start self-stretch p-0 font-inter">
            <div
              className="order-0 bg-primary-bg flex h-9 w-[288px] flex-none flex-grow-0 cursor-pointer flex-row items-start gap-2 self-stretch px-0 py-2 transition-colors hover:bg-[#373C42]"
              onClick={handleBuyerToggle}
            >
              <span className="order-1 h-5 w-[288px] flex-none flex-grow font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white">
                Conversation: Coffee Buying
              </span>
              <ChevronUp
                className={`order-2 hidden h-5 w-5 flex-none flex-grow-0 transition-transform ${
                  isBuyerExpanded ? "rotate-0" : "rotate-180"
                }`}
              />
            </div>

            {isBuyerExpanded && (
              <div className="order-1 flex h-[452px] w-[288px] flex-none flex-grow-0 flex-col items-start gap-2 self-stretch p-0">
                <div className="order-0 flex h-36 w-[288px] flex-none flex-grow-0 flex-col items-start self-stretch p-0">
                  <div className="flex h-9 w-[288px] items-center gap-2 py-2 pl-3 pr-2 transition-colors hover:bg-[#373C42]">
                    <span className="h-5 w-[208px] font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white opacity-100">
                      Agentic Patterns
                    </span>
                  </div>

                  <div>
                    <SidebarDropdown
                      title="Transport"
                      isExpanded={isTransportExpanded}
                      onToggle={handleTransportToggle}
                      isNested={true}
                    >
                      <SidebarItem
                        title="Multi SLIM A2A"
                        isSelected={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                        onClick={() => onPatternChange(PATTERNS.SLIM_MULTI_A2A)}
                      />
                    </SidebarDropdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
