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

      <div className="bg-modal-background border-modal-border absolute right-4 top-16 w-80 rounded-lg border shadow-lg">
        <button
          onClick={onClose}
          className="text-modal-text-secondary hover:bg-modal-hover absolute right-2 top-2 rounded-lg p-1 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="space-y-4 p-4 pr-10">
          <div>
            <h3 className="text-modal-text mb-3 text-sm font-normal leading-5 tracking-wide">
              Build and Release Information
            </h3>
            <div className="text-modal-text-secondary space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Release Version:</span>
                <span className="text-modal-accent font-mono">0.0.030</span>
              </div>
              <div className="flex justify-between">
                <span>Build Date:</span>
                <span className="font-mono">August 22, 2025</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-modal-text mb-3 text-sm font-normal leading-5 tracking-wide">
              Dependencies:
            </h3>
            <div className="text-modal-text-secondary space-y-2 text-sm">
              <div className="flex justify-between">
                <span>AGNTCY App SDK:</span>
                <span className="text-modal-accent font-mono">v0.1.4</span>
              </div>
              <div className="flex justify-between">
                <span>SLIM:</span>
                <span className="text-modal-accent font-mono">v0.3.15</span>
              </div>
              <div className="flex justify-between">
                <span>Observe SDK:</span>
                <span className="text-modal-accent font-mono">v1.0.12</span>
              </div>
              <div className="flex justify-between">
                <span>A2A:</span>
                <span className="text-modal-accent font-mono">v0.2.5</span>
              </div>
              <div className="flex justify-between">
                <span>MCP:</span>
                <span className="text-modal-accent font-mono">
                  &gt;= v1.10.0
                </span>
              </div>
              <div className="flex justify-between">
                <span>LangGraph:</span>
                <span className="text-modal-accent font-mono">
                  &gt;= v0.4.1
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfoModal
