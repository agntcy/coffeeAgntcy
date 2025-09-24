/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { X } from "lucide-react"

interface InfoModalProps {
  isOpen: boolean
  onClose: () => void
}

const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose }) => {
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
              <div className="flex justify-between">
                <span>Release Version:</span>
                <span className="font-mono text-modal-accent">0.0.037</span>
              </div>
              <div className="flex justify-between">
                <div className="flex justify-between">
                  <span>Build Date:</span>
                  <span className="font-mono">September 9, 2025</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-sm font-normal leading-5 tracking-wide text-modal-text">
                Dependencies:
              </h3>
              <div className="space-y-2 text-sm text-modal-text-secondary">
                <div className="flex justify-between">
                  <span>AGNTCY App SDK:</span>
                  <span className="font-mono text-modal-accent"> v0.2.0</span>
                </div>
                <div className="flex justify-between">
                  <span>SLIM:</span>
                  <span className="font-mono text-modal-accent">v0.4.0</span>
                </div>
                <div className="flex justify-between">
                  <span>Observe SDK:</span>
                  <span className="font-mono text-modal-accent">v1.0.15</span>
                </div>
                <div className="flex justify-between">
                  <span>A2A:</span>
                  <span className="font-mono text-modal-accent">v0.2.16</span>
                </div>
                <div className="flex justify-between">
                  <span>Identity:</span>
                  <span className="font-mono text-modal-accent">v0.0.2</span>
                </div>
                <div className="flex justify-between">
                  <span>MCP:</span>
                  <span className="font-mono text-modal-accent">
                    &gt;= v1.10.0
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>LangGraph:</span>
                  <span className="font-mono text-modal-accent">
                    &gt;= v0.4.1
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfoModal
