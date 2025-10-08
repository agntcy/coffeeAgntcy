/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useState } from "react"
import { X } from "lucide-react"

interface InfoModalProps {
  isOpen: boolean
  onClose: () => void
}

interface BuildInfo {
  app: string
  service: string
  version: string
  build_date: string
  build_timestamp: string
  image: string
  dependencies: Record<string, string>
}

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL

const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose }) => {
  const [info, setInfo] = useState<BuildInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    let cancelled = false
    const fetchInfo = async () => {
      try {
        setError(null)
        const res = await fetch(`${EXCHANGE_APP_API_URL}/about`)
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        const data = await res.json()
        if (!cancelled) setInfo(data)
      } catch (e) {
        if (!cancelled) setError("Failed to load build info")
      }
    }
    fetchInfo()
    return () => {
      cancelled = true
    }
  }, [isOpen, EXCHANGE_APP_API_URL])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0" onClick={onClose} />

      <div className="absolute right-4 top-16 w-80 rounded-lg border border-modal-border bg-modal-background shadow-lg">
        <button
          onClick={onClose}
          className="absolute right-2 top-2 rounded-lg p-1 text-modal-text-secondary transition-colors hover:bg-modal-hover"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="space-y-4 p-4 pr-10">
          <div>
            <h3 className="mb-3 text-sm font-normal leading-5 tracking-wide text-modal-text">
              Build and Release Information
            </h3>
            <div className="space-y-2 text-sm text-modal-text-secondary">
              {error && <div className="text-red-500">{error}</div>}
              <div className="flex justify-between">
                <span>Release Version:</span>
                <span className="font-mono text-modal-accent">
                  {info?.version ?? "…"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Build Date:</span>
                <span className="font-mono">{info?.build_date ?? "…"}</span>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-sm font-normal leading-5 tracking-wide text-modal-text">
                Dependencies:
              </h3>
              <div className="space-y-2 text-sm text-modal-text-secondary">
                {info ? (
                  Object.entries(info.dependencies).map(([k, v]) => (
                    <div className="flex justify-between" key={k}>
                      <span>{k}:</span>
                      <span className="font-mono text-modal-accent">{v}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-modal-text-secondary">Loading…</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfoModal
