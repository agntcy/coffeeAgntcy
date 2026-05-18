/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Helpers that build opaque keys for Sidebar expand/collapse state.
 */

export const REFERENCE_LIBRARY_KEY = "reference-library"

export const makePatternKey = (patternName: string): string =>
  `pattern:${patternName}`

export const makeScenarioKey = (
  patternName: string,
  useCase: string,
  scenario: string,
): string => `pattern:${patternName}|usecase:${useCase}|scenario:${scenario}`

/** Expandable workflow header (SLIM transport workflows only). */
export const makeWorkflowKey = (
  patternName: string,
  useCase: string,
  scenario: string,
  workflowName: string,
): string =>
  `pattern:${patternName}|usecase:${useCase}|scenario:${scenario}|workflow:${workflowName}`
