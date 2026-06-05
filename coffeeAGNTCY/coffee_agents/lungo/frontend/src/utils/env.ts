/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared utility for Vite env: use this instead of import.meta.env directly
 * so all env access is centralized and testable.
 **/

declare global {
  interface Window {
    __ENV__?: Readonly<Record<string, string>>
  }
}

const rawEnv = import.meta.env

function runtimeEnv(key: string): string | undefined {
  if (typeof window === "undefined") return undefined
  const v = window.__ENV__?.[key]
  return typeof v === "string" && v !== "" ? v : undefined
}

export function getEnvValueByKey(key: string): string | undefined {
  return (
    runtimeEnv(key) ??
    (typeof rawEnv[key] === "string" && rawEnv[key] !== ""
      ? rawEnv[key]
      : undefined)
  )
}

/** Optional convenience at call sites */
export function envOrDefault(key: string, defaultValue: string): string {
  return getEnvValueByKey(key) ?? defaultValue
}

/** True when running in Vite dev server. */
export function isDev(): boolean {
  return Boolean(rawEnv.DEV)
}

/** Vite mode (e.g. "development", "production"). */
export function getMode(): string {
  return typeof rawEnv.MODE === "string" ? rawEnv.MODE : ""
}

/** Env helper object for convenient access. */
export const env = {
  get: getEnvValueByKey,
  get dev(): boolean {
    return isDev()
  },
  get mode(): string {
    return getMode()
  },
} as const
