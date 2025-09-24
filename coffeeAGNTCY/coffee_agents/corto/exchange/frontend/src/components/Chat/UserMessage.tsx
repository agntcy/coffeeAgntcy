/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { User } from "lucide-react"

interface UserMessageProps {
  content: string
}

const UserMessage: React.FC<UserMessageProps> = ({ content }) => {
  return (
    <div className="flex min-h-[2.5rem] w-full flex-row items-start gap-1">
      <div className="chat-avatar-container flex h-10 w-10 flex-none items-center justify-center rounded-full bg-action-background">
        <User size={22} className="text-white" />
      </div>

      <div
        className="flex min-h-[2.5rem] flex-1 flex-col items-start justify-center rounded p-1 px-2"
        style={{ maxWidth: "calc(100% - 3rem)" }}
      >
        <div className="flex w-full items-center rounded p-1 px-2">
          <div className="break-words font-inter text-sm font-normal leading-5 text-chat-text">
            {content}
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserMessage
