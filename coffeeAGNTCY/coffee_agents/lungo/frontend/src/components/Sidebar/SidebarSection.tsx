/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ChevronUp } from "lucide-react"

interface SidebarSectionProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

const SidebarSection: React.FC<SidebarSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  return (
    <div className="h-18 order-0 flex w-72 flex-none grow-0 flex-col items-start self-stretch p-0">
      <div
        className="order-0 flex h-9 w-[288px] flex-none flex-grow-0 cursor-pointer flex-row items-start gap-2 self-stretch bg-sidebar-background px-0 py-2 font-inter"
        onClick={onToggle}
      >
        <div className="order-0 hidden h-5 w-5 flex-none flex-grow-0" />

        <span className="order-1 h-5 w-[288px] flex-none flex-grow font-inter text-sm font-normal leading-5 tracking-normal text-white">
          {title}
        </span>
        <ChevronUp
          className={`order-2 hidden h-5 w-5 flex-none flex-grow-0 text-white transition-transform ${
            isExpanded ? "rotate-0" : "rotate-180"
          }`}
        />
      </div>

      {isExpanded && <div className="flex flex-col">{children}</div>}
    </div>
  )
}

export default SidebarSection
