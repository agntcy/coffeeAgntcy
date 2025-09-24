/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

interface SidebarItemProps {
  title: string
  isSelected?: boolean
  onClick?: () => void
  className?: string
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  title,
  isSelected = false,
  onClick,
  className = "",
}) => {
  return (
    <div
      className={`flex h-9 w-full cursor-pointer items-start gap-2 px-5 py-2 pl-12 font-inter text-sm font-normal leading-5 text-sidebar-text transition-colors hover:bg-sidebar-item-selected ${isSelected ? "bg-sidebar-item-selected" : "bg-sidebar-background"} ${className}`}
      onClick={onClick}
    >
      <span className="flex-1">{title}</span>
    </div>
  )
}

export default SidebarItem
