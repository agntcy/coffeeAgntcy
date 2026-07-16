/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { env } from "@/utils/env"
import { logger, unsafeLogger } from "@/utils/logger"
import {
  type ErrorNotificationSeverity,
  useErrorNotificationStore,
} from "./errorNotificationStore"

export type ReportUiErrorInput = {
  title?: string
  message: string
  severity?: ErrorNotificationSeverity
  source?: string
}

const DEFAULT_UI_ERROR_TITLE = "Something went wrong"

/**
 * Surface a non-request UI failure to users via the global notification banner.
 */
export function reportUiError(input: ReportUiErrorInput): string {
  const log = env.dev ? logger : unsafeLogger
  const title = input.title ?? DEFAULT_UI_ERROR_TITLE

  log.error(`UI Error - ${title}`, {
    message: input.message,
    source: input.source,
    severity: input.severity ?? "error",
  })

  return useErrorNotificationStore.getState().pushError({
    title,
    message: input.message,
    severity: input.severity,
    source: input.source,
  })
}
