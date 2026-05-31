/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * LHS catalog tree depth: pattern → use case → scenario → workflow (leaf).
 */

export enum CatalogTreeLevel {
  Pattern = 0,
  UseCase = 1,
  Scenario = 2,
  Workflow = 3,
}

/** Left padding per tree level (px). */
export const SIDEBAR_LEVEL_INDENT_PX = 2

export const sidebarLevelIndentPx = (level: number): string =>
  `${level * SIDEBAR_LEVEL_INDENT_PX}px`
