/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export interface Prompt {
    prompt: string
    description: string
}

export interface PromptCategory {
    name: string
    prompts: Prompt[]
}