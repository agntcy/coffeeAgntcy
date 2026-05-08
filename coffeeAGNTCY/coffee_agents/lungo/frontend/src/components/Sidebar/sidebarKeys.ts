/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Helpers that build the opaque keys used by the Sidebar to track which
 * pattern and use-case+scenario rows are currently expanded.
 */

export const makePatternKey = (patternName: string): string =>
  `pattern:${patternName}`

export const makeScenarioKey = (
  patternName: string,
  useCase: string,
  scenario: string,
): string => `pattern:${patternName}|usecase:${useCase}|scenario:${scenario}`
