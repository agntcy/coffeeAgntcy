/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Box, Stack } from "@open-ui-kit/core"
import { LoadingSpinner } from "@/components/loading"

export interface FeedSpinnerRowProps {
  mt?: number
}

export function FeedSpinnerRow({ mt = 3 }: FeedSpinnerRowProps) {
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      spacing={0.5}
      sx={{ mt, width: "100%" }}
    >
      <Box sx={{ mt: 0.5, display: "flex", alignItems: "center" }} aria-hidden>
        <LoadingSpinner compact />
      </Box>
      <Box sx={{ flex: 1 }} />
    </Stack>
  )
}
