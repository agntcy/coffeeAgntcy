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
    <div className="flex h-10 w-[880px] flex-row items-start gap-1">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#00142B]">
        <User size={22} className="text-white" />
      </div>

      <div className="flex h-10 w-[814px] flex-col items-start justify-center rounded p-1 px-2">
        <div className="flex h-10 w-[814px] items-center rounded p-1 px-2">
          <div className="font-inter text-sm font-normal leading-5 text-white">
            {content}
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserMessage
