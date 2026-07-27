/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * OUK Large negative EmptyState illustrations render at 224px; use 56px (¼)
 * for graph/modal errors. Target the illustration with :first-child — :first-of-type
 * matches the text stack div, not the svg icon.
 */

import { GeneralSize } from "@open-ui-kit/core"
import type { EmptyStateProps } from "@open-ui-kit/core"

const OUK_LARGE_NEGATIVE_ILLUSTRATION_PX = 224

const compactNegativeEmptyStateIconPx = OUK_LARGE_NEGATIVE_ILLUSTRATION_PX / 4

export const compactNegativeEmptyStateProps: Pick<
  EmptyStateProps,
  "direction" | "size" | "containerProps"
> = {
  direction: "column",
  size: GeneralSize.Large,
  containerProps: {
    sx: {
      width: "100%",
      flexDirection: "column",
      alignItems: "center",
      "& > :first-child": {
        width: `${compactNegativeEmptyStateIconPx}px`,
        height: `${compactNegativeEmptyStateIconPx}px`,
        flexShrink: 0,
      },
    },
  },
}
