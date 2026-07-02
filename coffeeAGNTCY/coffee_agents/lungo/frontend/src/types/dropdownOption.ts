/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Local dropdown option shape (formerly exported as DropdownOption from OUK 1.x).
 */

import type { ReactNode } from "react"
import type { TooltipProps } from "@open-ui-kit/core"

export interface DropdownOption<T = string> {
  label: string
  value: T
  customElement?: ReactNode
  menuItemTooltipProps?: Partial<TooltipProps>
}
