/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { ReactNode } from "react"
import { Message } from "@open-ui-kit/core"

export interface FeedErrorMessageProps {
  children: ReactNode
}

/** Inline streaming feed error using OUK Message (connection / stream failures). */
export function FeedErrorMessage({ children }: FeedErrorMessageProps) {
  return (
    <Message
      type="error"
      hideClose
      role="alert"
      title="Connection error"
      sx={{ width: "100%" }}
    >
      {children}
    </Message>
  )
}
