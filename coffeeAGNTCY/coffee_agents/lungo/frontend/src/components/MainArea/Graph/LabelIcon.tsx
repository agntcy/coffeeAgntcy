/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { RiShieldCheckFill } from "react-icons/ri"
import a2aIcon from "@/assets/a2a_icon.svg"
import mcpIcon from "@/assets/mcp_icon.png"
import { EdgeLabelIcon } from "@/utils/const"

interface LabelIconProps {
  type?: string
  altText?: string
  size?: number
}

const LabelIcon: React.FC<LabelIconProps> = ({
  type,
  altText = "icon",
  size = 16,
}) => {
  const isA2A = type === EdgeLabelIcon.A2A
  const isIdentity = type === EdgeLabelIcon.IDENTITY

  if (type === EdgeLabelIcon.A2A || type === EdgeLabelIcon.MCP) {
    const iconPath = type === EdgeLabelIcon.A2A ? a2aIcon : mcpIcon

    return (
      <div
        className="flex min-h-4 min-w-4 items-center justify-center overflow-hidden rounded-full bg-white"
        style={{ width: `${size}px`, height: `${size}px` }}
      >
        <img
          src={iconPath}
          alt={altText}
          className={`h-[85%] w-[85%] object-contain ${isA2A ? "opacity-80" : "opacity-100"}`}
        />
      </div>
    )
  }

  if (isIdentity) {
    return (
      <div
        className="flex min-h-4 min-w-4 items-center justify-center overflow-hidden rounded-full bg-white"
        style={{ width: `${size}px`, height: `${size}px` }}
      >
        <RiShieldCheckFill
          size={size * 0.7}
          color="#187ADC"
          className="opacity-90"
        />
      </div>
    )
  }

  return null
}

export default LabelIcon
