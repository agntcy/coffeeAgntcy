/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import ResizablePanelSeparator from "@/components/layout/ResizablePanelSeparator"

const SidebarPanelSeparator: React.FC = () => (
  <ResizablePanelSeparator
    id="sidebar-panel-separator"
    aria-label="Resize conversation catalog"
    orientation="horizontal"
  />
)

export default SidebarPanelSeparator
