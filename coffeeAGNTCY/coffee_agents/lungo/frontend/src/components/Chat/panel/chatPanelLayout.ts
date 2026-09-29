/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Resizable graph/chat panel ids and size constraints (react-resizable-panels).
 */

import {
  RESIZABLE_PANEL_MAX_SIZE,
  RESIZABLE_PANEL_MIN_SIZE,
} from "@/components/layout/resizablePanelLayout"

export const MAIN_VERTICAL_GROUP_ID = "main-vertical"

export const GRAPH_PANEL_ID = "graph"
export const CHAT_PANEL_ID = "chat"

/** Room for header, composer, and a short scrollable message area. */
export const CHAT_MIN_SIZE = "12rem"

export const CHAT_MAX_SIZE = RESIZABLE_PANEL_MAX_SIZE

/** Keeps at least a quarter of the main column for the graph when chat is tall. */
export const GRAPH_MIN_SIZE = RESIZABLE_PANEL_MIN_SIZE

export const CHAT_PANEL_AUTO_SIZE_MAX_ATTEMPTS = 10
