/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared types for the reference-library pattern-doc surface.
 * Placed in a leaf module so MainArea and useApp can both depend on
 * them without forming a cycle.
 */

export enum CanvasMode {
  WORKFLOW = "workflow",
  PATTERN_DOC = "pattern_doc",
  CATEGORY_DOC = "category_doc",
}

export type PatternDocStatus =
  | "idle"
  | "loading"
  | "ready"
  | "not_found"
  | "error"

/** Markdown payload rendered by the doc canvas, for a pattern or a category. */
export interface ReferenceDocumentation {
  name: string
  title: string
  pattern_category: string | null
  full_markdown: string
}

export interface PatternDocState {
  status: PatternDocStatus
  documentation: ReferenceDocumentation | null
  errorMessage: string | null
}
