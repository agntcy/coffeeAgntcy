/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"
import { fetchOasfRecord, OasfRecord } from "./DirectoryApi"
import { CustomNodeData } from "../Elements/types"
import { IdentityServiceError } from "../Identity/IdentityApi"
import { useEscapeKey } from "@/hooks/useEscapeKey"

export interface OasfRecordModalProps {
    isOpen: boolean
    onClose: () => void
    nodeName: string
    nodeData: CustomNodeData
    position: { x: number; y: number }
}

const Spinner: React.FC = () => (
    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-node-text-primary border-r-transparent"></div>
)

const OasfRecordModal: React.FC<OasfRecordModalProps> = ({
                                                             isOpen,
                                                             onClose,
                                                             nodeName,
                                                             nodeData,
                                                             position,
                                                         }) => {
    const [record, setRecord] = useState<OasfRecord | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (isOpen && nodeData) {
            console.log("[OasfRecordModal] Opening modal for node:", nodeData);
            fetchOasfRecordData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, nodeName, nodeData])

    useEscapeKey(isOpen, onClose)

    const fetchOasfRecordData = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await fetchOasfRecord(nodeData)
            setRecord(data)
        } catch (err) {
            const apiError = err as IdentityServiceError
            setError(
                apiError.message ||
                "An unexpected error occurred while fetching OASF record."
            )
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen) return null

    const handleModalClick = (e: React.MouseEvent) => e.stopPropagation()

    return createPortal(
        <div className="pointer-events-none fixed inset-0 z-50">
            <div
                className="pointer-events-auto absolute -translate-x-1/2"
                style={{ left: `${position.x}px`, top: `${position.y}px` }}
            >
                <div
                    className="relative flex max-h-[40vh] w-[575px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
                    onClick={handleModalClick}
                    data-modal-content
                >
                    <button
                        onClick={onClose}
                        className="absolute right-3 top-3 z-10 text-xl leading-none text-node-text-secondary transition-colors hover:text-node-text-primary"
                    >
                        ×
                    </button>
                    {loading && !record ? (
                        <div className="flex w-full items-center justify-center py-8">
                            <Spinner />
                        </div>
                    ) : error ? (
                        <div className="flex w-full flex-col items-center justify-center gap-4 py-8">
                            <div className="text-center text-node-text-primary">
                                <p className="font-medium">Failed to load OASF record</p>
                                <p className="mt-2 text-sm text-node-text-secondary opacity-80">
                                    {error}
                                </p>
                            </div>
                            <button
                                onClick={fetchOasfRecordData}
                                className="rounded bg-node-icon-background px-4 py-2 text-sm text-node-text-primary hover:bg-opacity-80"
                            >
                                Retry
                            </button>
                        </div>
                    ) : record ? (
                        <div className="relative flex max-h-[26vh] min-h-0 w-full flex-col gap-3 overflow-y-auto">
                            <h3 className="mb-3 text-lg font-semibold text-node-text-primary">
                                {nodeName} OASF Record
                            </h3>
                            <pre className="overflow-auto whitespace-pre-wrap rounded border border-gray-600 p-3 font-mono text-xs text-node-text-primary">
                {JSON.stringify(record, null, 2)}
              </pre>
                            {loading && (
                                <div className="absolute inset-0 flex items-center justify-center bg-node-background bg-opacity-80 backdrop-blur-sm">
                                    <Spinner />
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex w-full items-center justify-center py-8">
                            <div className="text-node-text-primary">No data available</div>
                        </div>
                    )}
                </div>
            </div>
        </div>,
        document.body
    )
}

export default OasfRecordModal
