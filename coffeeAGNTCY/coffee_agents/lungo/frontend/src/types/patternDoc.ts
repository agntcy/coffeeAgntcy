/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared types for the reference-library pattern-doc surface.
 * Placed in a leaf module so MainArea and useApp can both depend on
 * them without forming a cycle.
 */

import type { WorkflowDocumentation } from "@/utils/agenticWorkflowsApi"

export enum CanvasMode {
  WORKFLOW = "workflow",
  PATTERN_DOC = "pattern_doc",
}

export type PatternDocStatus =
  | "idle"
  | "loading"
  | "ready"
  | "not_found"
  | "error"

export interface PatternDocState {
  status: PatternDocStatus
  documentation: WorkflowDocumentation | null
  errorMessage: string | null
}
