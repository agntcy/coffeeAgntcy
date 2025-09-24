/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Trash2 } from "lucide-react"
import collapseIcon from "@/assets/collapse.png"

interface ChatHeaderProps {
  onMinimize?: () => void
  onClearConversation?: () => void
  isMinimized?: boolean
  showActions?: boolean
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  onMinimize,
  onClearConversation,
  isMinimized,
  showActions = false,
}) => {
  if (!showActions) {
    return null
  }

  return (
    <div
      className="flex w-full items-center justify-end px-2 py-2 sm:px-4 md:px-8 lg:px-4"
      style={{ borderBottom: "1px solid var(--control-border-weak)" }}
    >
      <div className="flex items-center gap-2">
        {onMinimize && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg p-1">
            <button
              onClick={onMinimize}
              className="flex h-5 w-5 items-center justify-center rounded transition-colors"
              title={isMinimized ? "Maximize" : "Minimize"}
            >
              <img
                src={collapseIcon}
                alt={isMinimized ? "Maximize" : "Minimize"}
                className={`chat-header-icon h-5 w-5 ${isMinimized ? "rotate-180" : ""}`}
              />
            </button>
          </div>
        )}
        {onClearConversation && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg p-1">
            <button
              onClick={onClearConversation}
              className="flex h-5 w-5 items-center justify-center rounded transition-colors"
              title="Clear conversation"
            >
              <Trash2 className="chat-header-trash-icon h-5 w-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatHeader
