/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Expandable workflow header under a conversation row. Not selectable;
 * the child "A2A SLIM" row handles selection and documentation.
 **/

import React from "react"
import { cn } from "@/utils/cn"

interface WorkflowDropdownProps {
  title: string
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
  isChildSelected?: boolean
}

const WorkflowDropdown: React.FC<WorkflowDropdownProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
  isChildSelected = false,
}) => {
  return (
    <div className="flex w-full flex-col items-start p-0">
      <div
        className={cn(
          "flex w-full items-start gap-2 bg-sidebar-background py-2 pl-8 pr-5 transition-colors hover:bg-sidebar-item-selected",
          isChildSelected && "bg-sidebar-item-selected",
        )}
      >
        <span
          className="flex-1 cursor-pointer font-inter text-sm font-normal leading-5 tracking-[0.25px] text-sidebar-text"
          onClick={onToggle}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onToggle()
            }
          }}
          role="button"
          tabIndex={0}
          aria-expanded={isExpanded}
        >
          {title}
        </span>
      </div>
      {isExpanded && <div className="flex w-full flex-col">{children}</div>}
    </div>
  )
}

export default WorkflowDropdown
