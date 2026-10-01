/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"

import ResizablePanelSeparator from "@/components/layout/ResizablePanelSeparator"

type ChatPanelSeparatorProps = {
  disabled?: boolean
}

const ChatPanelSeparator: React.FC<ChatPanelSeparatorProps> = ({
  disabled = false,
}) => (
  <ResizablePanelSeparator
    id="chat-panel-separator"
    aria-label="Resize agent chat"
    orientation="vertical"
    disabled={disabled}
  />
)

export default ChatPanelSeparator
