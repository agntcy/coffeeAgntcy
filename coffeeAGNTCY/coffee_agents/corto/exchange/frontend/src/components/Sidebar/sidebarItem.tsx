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
      className={`flex h-9 w-80 cursor-pointer items-center gap-2 py-2 pb-2 pl-12 pr-5 font-inter text-sm font-normal leading-5 tracking-normal text-white opacity-100 ${isSelected ? "bg-sidebar-item-selected" : "bg-transparent"} ${className}`}
      onClick={onClick}
    >
      {title}
    </div>
  )
}

export default SidebarItem
