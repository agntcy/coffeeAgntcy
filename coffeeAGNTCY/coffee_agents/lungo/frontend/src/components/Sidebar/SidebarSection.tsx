/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

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
      <div className="order-0 flex h-9 w-[288px] flex-none flex-grow-0 flex-row items-start gap-2 self-stretch bg-sidebar-background px-0 py-2 font-inter">
        <div className="order-0 hidden h-5 w-5 flex-none flex-grow-0" />

        <span
          className="order-1 h-5 w-[288px] flex-none flex-grow cursor-pointer font-inter text-sm font-normal leading-5 tracking-normal text-white"
          onClick={onToggle}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onToggle()
            }
          }}
          role="button"
          tabIndex={0}
        >
          {title}
        </span>
      </div>

      {isExpanded && <div className="flex flex-col">{children}</div>}
    </div>
  )
}

export default SidebarSection
