/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Vector AGNTCY Directory “A” (same silhouette as the raster badge).
 * Uses currentColor so graph side-control chrome can paint it like Github / identity.
 */

import SvgIcon, { type SvgIconProps } from "@mui/material/SvgIcon"

/** Path from `src/assets/agent_directory_a.svg`. */
const DIRECTORY_A_PATH =
  "M2.5 22L7.04 6.87L8.39 4.02L10.07 2.5L12.08 2H21.5V22H15.11L14.94 16.96H10.74L9.23 22H2.67L2.5 22ZM12.08 11.92H14.94L14.77 6.87H14.1L13.43 7.38L12.25 11.75L12.08 11.92Z"

export function DirectoryAIcon(props: SvgIconProps) {
  return (
    <SvgIcon viewBox="0 0 24 24" aria-hidden {...props}>
      <g transform="translate(12 12) scale(0.85) translate(-12 -12)">
        <path
          fill="currentColor"
          fillRule="evenodd"
          clipRule="evenodd"
          d={DIRECTORY_A_PATH}
        />
      </g>
    </SvgIcon>
  )
}
