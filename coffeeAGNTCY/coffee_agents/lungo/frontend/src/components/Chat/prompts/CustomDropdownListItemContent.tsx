/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Stack, Typography } from "@open-ui-kit/core"

const dropdownItemTextSx = {
  whiteSpace: "normal" as const,
  overflowWrap: "anywhere" as const,
  wordBreak: "break-word" as const,
}

export interface CustomDropdownListItemContentProps {
  prompt: string
  description?: string
}

export const CustomDropdownListItemContent: React.FC<
  CustomDropdownListItemContentProps
> = ({ prompt, description }) => {
  return (
    <Stack direction="column" sx={{ minWidth: 0, width: "100%" }}>
      <Typography variant="body1Semibold" sx={dropdownItemTextSx}>
        {prompt}
      </Typography>
      {description ? (
        <Typography variant="body1" sx={dropdownItemTextSx}>
          {description}
        </Typography>
      ) : null}
    </Stack>
  )
}
