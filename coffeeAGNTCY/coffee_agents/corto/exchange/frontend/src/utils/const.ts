/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

export const Role = {
  ASSISTANT: "assistant",
  USER: "user",
} as const
export type RoleType = (typeof Role)[keyof typeof Role]

export type ApiErrorInfo = {
  status?: number
  message: string
}

export const parseApiError = (error: any): ApiErrorInfo => {
  if (error?.response) {
    const status = error.response.status
    const data = error.response.data

    return {
      status,
      message:
        typeof data === "string"
          ? data
          : data?.message || "Request failed",
    }
  }

  return {
    message: "Sorry, something went wrong. Please try again later.",
  }
}
