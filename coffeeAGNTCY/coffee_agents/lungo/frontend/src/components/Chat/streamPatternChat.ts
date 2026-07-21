/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import { reportRequestError } from "@/errors/request"
import {
  PatternChatNotFoundError,
  PatternChatTransportError,
  type PatternChatCallbacks,
  type PatternChatRequest,
} from "@/hooks/chat"

export interface StreamPatternChatParams {
  patternName: string
  sessionId: string
  message: string
  send: (
    req: PatternChatRequest,
    callbacks: PatternChatCallbacks,
  ) => Promise<void>
  onUserInput?: (message: string) => void
  onApiResponse?: (text: string, isError: boolean) => void
  onStart: () => void
  onSettled: () => void
  onSuccess: () => void
}

export const streamPatternChat = async ({
  patternName,
  sessionId,
  message,
  send,
  onUserInput,
  onApiResponse,
  onStart,
  onSettled,
  onSuccess,
}: StreamPatternChatParams): Promise<void> => {
  onStart()
  onUserInput?.(message)

  let acc = ""
  await send(
    { patternName, sessionId, message },
    {
      onChunk: (chunk) => {
        acc += chunk
        onApiResponse?.(acc, false)
      },
      onDone: () => {
        onSuccess()
        onSettled()
      },
      onError: (err) => {
        reportRequestError("/patterns/{name}/chat", err)
        const msg =
          err instanceof PatternChatNotFoundError
            ? `No documentation chat available for "${patternName}" yet.`
            : err instanceof PatternChatTransportError
              ? `Network error: ${err.message}`
              : err.message || "The pattern chat failed."
        onApiResponse?.(msg, true)
        onSettled()
      },
    },
  )
}
