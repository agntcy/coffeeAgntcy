/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
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

  const handleTransportToggle = () => {
    setIsTransportExpanded(!isTransportExpanded)
  }

  return (
    <div className="flex h-full w-[320px] flex-col items-start gap-5 border-r border-[#00142B] bg-primary-bg px-4 py-0 font-inter">
      <div className="mt-5 flex w-[288px] flex-col items-start gap-0 p-0">
        <div className="flex w-[288px] flex-col items-start p-0">
          <div className="flex h-9 w-[288px] items-start gap-2 bg-primary-bg p-2 transition-colors hover:bg-[#373C42]">
            <span className="flex-1 font-inter text-sm font-normal leading-5 tracking-[0.25px] text-white">
              Conversation: Coffee Buying
            </span>
          </div>

          <div className="flex w-[288px] flex-col items-start gap-0 p-0">
            <div className="flex h-9 w-[288px] items-start gap-2 bg-primary-bg px-5 py-2 transition-colors hover:bg-[#373C42]">
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
                  title="A2A SLIM"
                  isSelected={selectedPattern === PATTERNS.SLIM_MULTI_A2A}
                  onClick={() => onPatternChange(PATTERNS.SLIM_MULTI_A2A)}
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
