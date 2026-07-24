/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export interface Prompt {
  prompt: string
  description: string
}

/** Single entry in a suggested-prompts category list (wire may omit fields). */
export type SuggestedPromptsPromptWire = {
  prompt?: string
  description?: string
}

/** GET /suggested-prompts JSON body: category name → prompt entries. */
export type SuggestedPromptsResponse = Record<
  string,
  SuggestedPromptsPromptWire[]
>

export interface PromptCategory {
  name: string
  prompts: Prompt[]
}
