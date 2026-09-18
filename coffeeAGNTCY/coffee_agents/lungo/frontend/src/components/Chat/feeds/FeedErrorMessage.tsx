/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { ReactNode } from "react"
import { Banner } from "@open-ui-kit/core"

export interface FeedErrorMessageProps {
  children: ReactNode
}

/** Inline streaming feed error (connection / stream failures). */
export function FeedErrorMessage({ children }: FeedErrorMessageProps) {
  return (
    <Banner
      status="negative"
      role="alert"
      sx={{ width: "100%" }}
      text={
        <>
          <strong>Connection error</strong>
          <br />
          {children}
        </>
      }
    />
  )
}
