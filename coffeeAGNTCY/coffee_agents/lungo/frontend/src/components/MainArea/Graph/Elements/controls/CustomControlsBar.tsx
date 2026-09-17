/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Horizontal graph controls shown below the canvas on compact viewports.
 */

import React from "react"
import { Box } from "@open-ui-kit/core"
import { graphControlsBarSx } from "./graphControlsBarSx"
import GraphControlButtons, {
  type GraphControlButtonsProps,
} from "./GraphControlButtons"

type CustomControlsBarProps = Pick<
  GraphControlButtonsProps,
  "isInteractive" | "onToggleInteractivity"
>

const CustomControlsBar: React.FC<CustomControlsBarProps> = ({
  isInteractive,
  onToggleInteractivity,
}) => (
  <Box
    component="nav"
    aria-label="Graph canvas controls"
    sx={graphControlsBarSx}
  >
    <GraphControlButtons
      direction="row"
      tooltipPlacement="top"
      buttonVariant="bar"
      stackSx={{ width: "100%", justifyContent: "space-between" }}
      isInteractive={isInteractive}
      onToggleInteractivity={onToggleInteractivity}
    />
  </Box>
)

export default CustomControlsBar
