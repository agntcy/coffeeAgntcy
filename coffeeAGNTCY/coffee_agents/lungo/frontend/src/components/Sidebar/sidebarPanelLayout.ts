/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Resizable app-shell panel ids and size constraints (react-resizable-panels).
 **/

import { RESIZABLE_PANEL_MAX_SIZE } from "@/components/layout/resizablePanelLayout"

export const APP_SHELL_PANEL_GROUP_ID = "app-shell"

export const SIDEBAR_PANEL_ID = "sidebar"
export const MAIN_PANEL_ID = "main"

/** Matches the previous fixed drawer width. */
export const SIDEBAR_DEFAULT_SIZE = "16.5rem"
export const SIDEBAR_MIN_SIZE = "14rem"
export const SIDEBAR_MAX_SIZE = RESIZABLE_PANEL_MAX_SIZE

/** Min share of shell width for graph + chat (lower than graph/chat vertical mins). */
export const MAIN_MIN_SIZE = "10%"
