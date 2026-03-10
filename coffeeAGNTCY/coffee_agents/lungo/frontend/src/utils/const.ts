/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import DOMPurify from "dompurify"
import { env } from "./env"

export const Role = {
  ASSISTANT: "assistant",
  USER: "user",
} as const

export const EdgeLabelIcon = {
  A2A: "a2a",
  MCP: "mcp",
} as const

export const EDGE_LABELS = {
  A2A: "A2A",
  MCP: "MCP: ",
  A2A_OVER_HTTP: "A2A: HTTP",
  MCP_WITH_STDIO: "MCP: stdio -> grpc",
} as const

export const FarmName = {
  BrazilCoffeeFarm: "Brazil Coffee Farm",
  ColombiaCoffeeFarm: "Colombia Coffee Farm",
  VietnamCoffeeFarm: "Vietnam Coffee Farm",
} as const

export const NODE_IDS = {
  AUCTION_AGENT: "1",
  TRANSPORT: "2",
  BRAZIL_FARM: "3",
  COLOMBIA_FARM: "4",
  VIETNAM_FARM: "5",
  WEATHER_MCP: "6",
  PAYMENT_MCP: "7",
  LOGISTICS_GROUP: "logistics-group",
  RECRUITER: "recruiter-agent",
  DIRECTORY: "agntcy-directory",
} as const

export const EDGE_IDS = {
  AUCTION_TO_TRANSPORT: "1-2",
  TRANSPORT_TO_BRAZIL: "2-3",
  TRANSPORT_TO_COLOMBIA: "2-4",
  TRANSPORT_TO_VIETNAM: "2-5",
  COLOMBIA_TO_MCP: "4-mcp",
  SUPERVISOR_TO_TRANSPORT: "1-2",
  FARM_TO_TRANSPORT: "3-2",
  TRANSPORT_TO_SHIPPER: "2-4",
  TRANSPORT_TO_ACCOUNTANT: "2-5",
  RECRUITER_TO_DIRECTORY: "recruiter-directory",
} as const

export const NODE_TYPES = {
  CUSTOM: "customNode",
  TRANSPORT: "transportNode",
  GROUP: "group",
} as const

export const EDGE_TYPES = {
  CUSTOM: "custom",
  BRANCHING: "branching",
} as const

export const HANDLE_TYPES = {
  SOURCE: "source",
  TARGET: "target",
  ALL: "all",
} as const

export const VERIFICATION_STATUS = {
  VERIFIED: "verified",
  FAILED: "failed",
} as const

export type RoleType = (typeof Role)[keyof typeof Role]
export type EdgeLabelIconType =
  (typeof EdgeLabelIcon)[keyof typeof EdgeLabelIcon]
export type FarmNameType = (typeof FarmName)[keyof typeof FarmName]
export type NodeIdType = (typeof NODE_IDS)[keyof typeof NODE_IDS]
export type EdgeIdType = (typeof EDGE_IDS)[keyof typeof EDGE_IDS]
export type NodeTypeType = (typeof NODE_TYPES)[keyof typeof NODE_TYPES]
export type EdgeTypeType = (typeof EDGE_TYPES)[keyof typeof EDGE_TYPES]
export type EdgeLabelType = (typeof EDGE_LABELS)[keyof typeof EDGE_LABELS]
export type HandleTypeType = (typeof HANDLE_TYPES)[keyof typeof HANDLE_TYPES]
export type VerificationStatusType =
  (typeof VERIFICATION_STATUS)[keyof typeof VERIFICATION_STATUS]

export const isLocalDev =
  env.dev ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"

export type ApiErrorInfo = {
  status?: number
  message: string
  raw?: unknown
}

/**
 * Strip HTML tags so the result is safe to render as text.
 * Used for API/backend error strings before display to prevent XSS if backend sends HTML.
 * Uses DOMPurify when DOM is available (accurate parsing); falls back to regex in Node (e.g. tests).
 */
export function stripHtml(html: string): string {
  if (typeof html !== "string" || html.length === 0) return html
  if (typeof window !== "undefined") {
    try {
      const out = DOMPurify.sanitize(html, { ALLOWED_TAGS: [] })
      return out.replace(/\s+/g, " ").trim()
    } catch {
      // fallback if DOMPurify fails (e.g. no DOM in tests)
    }
  }
  let out = html.replace(/<[^>]*>/g, " ")
  out = out.replace(/\s+/g, " ").trim()
  const entities: Record<string, string> = {
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
  }
  for (const [ent, char] of Object.entries(entities)) {
    out = out.split(ent).join(char)
  }
  out = out.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
  out = out.replace(/&#x([0-9a-fA-F]+);/g, (_, n) =>
    String.fromCharCode(parseInt(n, 16)),
  )
  return out
}

function getMessageFromUnknown(data: unknown): string {
  if (typeof data === "string") return stripHtml(data)
  if (data !== null && typeof data === "object") {
    const obj = data as Record<string, unknown>
    const msg = obj.message ?? obj.detail
    if (typeof msg === "string") {
      return stripHtml(msg)
    }
    return "Request failed"
  }
  return "Request failed"
}

export const parseApiError = (error: unknown): ApiErrorInfo => {
  if (
    error !== null &&
    typeof error === "object" &&
    "response" in error &&
    error.response !== null &&
    typeof error.response === "object"
  ) {
    const res = error.response as { status?: number; data?: unknown }
    const status = res.status
    const message = getMessageFromUnknown(res.data)
    return { status, message }
  }

  return {
    message: "Sorry, something went wrong. Please try again later.",
  }
}

export type FetchErrorInfo = { status: number; message: string }

export const parseFetchError = async (
  response: Response,
): Promise<FetchErrorInfo> => {
  const status = response.status
  let message = `HTTP ${response.status}: ${response.statusText}`

  try {
    const contentType = response.headers.get("content-type") ?? ""
    const raw = (await response.text()).trim() // read once

    if (!raw) return { status, message }

    if (contentType.includes("application/json")) {
      try {
        const body: unknown = JSON.parse(raw)

        if (body !== null && typeof body === "object" && !Array.isArray(body)) {
          const obj = body as Record<string, unknown>
          const detail = obj.detail
          const msg = obj.message
          const title = obj.title
          const errors = obj.errors
          const firstError =
            Array.isArray(errors) && errors.length > 0 ? errors[0] : undefined
          const fallback =
            typeof firstError === "string"
              ? firstError
              : firstError !== undefined
                ? String(firstError)
                : undefined
          message =
            (typeof detail === "string" ? detail : undefined) ??
            (typeof msg === "string" ? msg : undefined) ??
            (typeof title === "string" ? title : undefined) ??
            fallback ??
            JSON.stringify(body)
        } else if (typeof body === "string") {
          message = body
        }
      } catch {
        // Header says JSON but it's not valid JSON; fall back to raw text
        message = stripHtml(raw)
      }
    } else {
      message = stripHtml(raw)
    }
  } catch {
    // keep default message
  }

  return { status, message: stripHtml(message) }
}
