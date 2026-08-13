/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Panel } from "@xyflow/react"
import { Box } from "@open-ui-kit/core"
import GraphControlButtons, {
  type GraphControlButtonsProps,
} from "./GraphControlButtons"

type CustomControlsProps = Pick<
  GraphControlButtonsProps,
  "isInteractive" | "onToggleInteractivity"
>

const CustomControls: React.FC<CustomControlsProps> = ({
  isInteractive,
  onToggleInteractivity,
}) => (
  <Panel position="bottom-left">
    <Box component="nav" aria-label="Graph canvas controls">
      <GraphControlButtons
        direction="column"
        tooltipPlacement="right"
        stackSx={{ p: 1 }}
        isInteractive={isInteractive}
        onToggleInteractivity={onToggleInteractivity}
      />
    </Box>
  </Panel>
)

export default CustomControls
