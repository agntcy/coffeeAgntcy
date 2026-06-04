/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Stack, Typography } from "@open-ui-kit/core"

export interface CustomDropdownListItemContentProps {
  prompt: string
  description?: string
}

export const CustomDropdownListItemContent: React.FC<
  CustomDropdownListItemContentProps
> = ({ prompt, description }) => {
  return (
    <Stack direction="column">
      <Typography variant="body2">{prompt}</Typography>
      {description ? (
        <Typography variant="caption">{description}</Typography>
      ) : null}
    </Stack>
  )
}
