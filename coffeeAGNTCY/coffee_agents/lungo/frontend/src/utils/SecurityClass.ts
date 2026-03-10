/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

/** Allowed hostnames for http: URLs (localhost / dev only). */
const HTTP_ALLOWED_HOSTS = new Set(["localhost", "127.0.0.1"])

/**
 * Security utilities for URL validation and safe external navigation.
 * Use before passing URLs to href, window.open, or similar.
 */
export class SecurityClass {
  /**
   * Returns true only if the URL has a safe scheme for opening in a new tab/window.
   * Allows https: for any host. Allows http: only for localhost and 127.0.0.1.
   * Rejects javascript:, data:, file:, and invalid URLs.
   */
  static isSafeExternalUrl(url: string): boolean {
    if (typeof url !== "string" || !url.trim()) return false
    try {
      const parsed = new URL(url)
      if (parsed.protocol === "https:") return true
      if (parsed.protocol === "http:") {
        const host = parsed.hostname.toLowerCase()
        return HTTP_ALLOWED_HOSTS.has(host)
      }
      return false
    } catch {
      return false
    }
  }
}
