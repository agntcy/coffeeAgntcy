/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

const Sidebar: React.FC = () => {
  return (
    <div className="flex h-full w-64 flex-none flex-col border-r border-sidebar-border bg-sidebar-background font-inter lg:w-[320px]">
      <div className="flex h-full flex-1 flex-col gap-5 p-4">
        <div className="flex flex-col">
          <div className="flex min-h-[36px] w-full items-center gap-2 rounded p-2">
            <span className="flex-1 text-sm font-normal leading-5 tracking-wide text-sidebar-text">
              Conversation: Coffee Grading
            </span>
          </div>

          <div className="mt-1 rounded bg-sidebar-item-selected">
            <div className="flex min-h-[36px] w-full items-center gap-2 rounded bg-sidebar-item-selected p-2 pl-6">
              <span className="flex-1 text-sm font-normal leading-5 tracking-wide text-sidebar-text">
                Agent to Agent
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
