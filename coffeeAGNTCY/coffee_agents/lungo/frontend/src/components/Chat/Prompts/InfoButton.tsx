/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import { InformationCircleIcon, XMarkIcon } from "@heroicons/react/24/outline"
import ReactMarkdown from "react-markdown"

interface InfoButtonProps {
    infoContent: string
    className?: string
    iconSize?: number
}

const InfoButton: React.FC<InfoButtonProps> = ({
                                                   infoContent,
                                                   className,
                                                   iconSize = 16,
                                               }) => {
    const [showInfo, setShowInfo] = useState(false)

    const handleToggle = () => setShowInfo((prev) => !prev)
    const handleClose = () => setShowInfo(false)

    return (
        <div className={`relative ${className || ""}`}>
            {showInfo && (
                <div
                    className="absolute z-[1100] flex items-center gap-2 rounded p-2 shadow"
                    style={{
                        backgroundColor: "var(--info-bg)",
                        border: "1px solid var(--info-border)",
                    }}
                >
                    <div className="relative w-72 max-w-md">
                        <button
                            type="button"
                            className="absolute left-[-17.5px] top-[-17.5px] z-[1200] flex h-5 w-5 items-center justify-center rounded-full border hover:cursor-pointer"
                            style={{
                                borderColor: "var(--info-border)",
                                backgroundColor: "var(--info-bg)",
                            }}
                            onClick={handleClose}
                            aria-label="Close"
                            onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor =
                                    "var(--info-icon-bg-hover)"
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = "var(--info-bg)"
                            }}
                        >
                            <XMarkIcon className="h-3 w-3 text-[var(--info-text)]" />
                        </button>

                        <div
                            className="text-sm"
                            style={{ color: "var(--info-text)" }}
                        >
                            <ReactMarkdown>{infoContent}</ReactMarkdown>
                        </div>
                    </div>
                </div>
            )}

            <button
                type="button"
                className="absolute z-[1000] flex items-center justify-center rounded border px-0.5 py-0.5 hover:cursor-pointer"
                onClick={handleToggle}
                aria-label="More information"
                style={{
                    borderColor: "var(--info-icon-border)",
                    backgroundColor: "var(--info-icon-bg)",
                }}
                onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--info-icon-bg-hover)"
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--info-icon-bg)"
                }}
            >
                <InformationCircleIcon
                    style={{ width: iconSize, height: iconSize }}
                    className="text-[#00A0D1]"
                />
            </button>
        </div>
    )
}

export default InfoButton