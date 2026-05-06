/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Theme } from "@mui/material/styles"

/**
 * Single source of truth for “default” sidebar rounding.
 * Use this anywhere we explicitly set `borderRadius` (because the underlying component
 * doesn’t apply rounding by default, or we’re overriding it intentionally).
 */
export const sidebarBorderRadius = (theme: Theme) => theme.shape.borderRadius

/** Single source of truth for vertical spacing between sidebar rows. */
export const sidebarItemMt = 0.5
