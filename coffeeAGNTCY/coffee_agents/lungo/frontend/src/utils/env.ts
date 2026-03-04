/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared utility for Vite env: use this instead of import.meta.env directly
 * so all env access is centralized and testable.
 **/

const rawEnv = import.meta.env

/**
 * Get a string env value by key (e.g. VITE_DIRECTORY_SERVER_URL, VITE_DIRECTORY_VERSION).
 * Returns undefined if the key is missing or not a string.
 */
export function getEnvValueByKey(key: string): string | undefined {
  const v = rawEnv[key]
  return typeof v === "string" ? v : undefined
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
