/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"
import LoadingSpinner from "./LoadingSpinner"
import { PromptCategory } from "./PromptTypes"

const DEFAULT_DISCOVERY_APP_API_URL = "http://127.0.0.1:8882"
const DISCOVERY_APP_API_URL =
    import.meta.env.VITE_DISCOVERY_APP_API_URL || DEFAULT_DISCOVERY_APP_API_URL

interface DiscoveryPromptsDropdownProps {
    visible: boolean
    onSelect: (query: string) => void
}

const DiscoveryPromptsDropdown: React.FC<DiscoveryPromptsDropdownProps> = ({
                                                                               visible,
                                                                               onSelect,
                                                                           }) => {
    const [isOpen, setIsOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [categories, setCategories] = useState<PromptCategory[]>([])
    const dropdownRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const controller = new AbortController()
        let retryTimeoutId: NodeJS.Timeout | null = null
        const MAX_RETRY_DELAY = 5000

        const fetchPrompts = async (retryCount = 0) => {
            try {
                setIsLoading(true)
                const res = await fetch(`${DISCOVERY_APP_API_URL}/suggested-prompts`, {
                    cache: "no-cache",
                    signal: controller.signal,
                })

                if (!res.ok) throw new Error(`HTTP ${res.status}`)

                const data: unknown = await res.json()

                if (data && typeof data === "object") {
                    const nextCategories = Object.entries(data as Record<string, unknown>).map(
                        ([key, value]) => ({
                            name: key,
                            prompts: Array.isArray(value) ? (value as any[]) : [],
                        }),
                    )

                    setCategories(nextCategories)

                    if (nextCategories.every((category) => category.prompts.length === 0)) {
                        const delay = Math.min(5000 * Math.pow(2, retryCount), MAX_RETRY_DELAY)
                        retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
                    } else {
                        setIsLoading(false)
                    }
                } else {
                    setIsLoading(false)
                }
            } catch (err: unknown) {
                if (err instanceof Error && err.name !== "AbortError") {
                    const delay = Math.min(5000 * Math.pow(2, retryCount), MAX_RETRY_DELAY)
                    retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
                }
            } finally {
                setIsLoading(false)
            }
        }

        fetchPrompts()

        return () => {
            controller.abort()
            if (retryTimeoutId) clearTimeout(retryTimeoutId)
        }
    }, [])

    useEffect(() => {
        if (!visible || !isOpen) return

        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }

        const handleEscapeKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setIsOpen(false)
            }
        }

        document.addEventListener("mousedown", handleClickOutside, true)
        document.addEventListener("keydown", handleEscapeKey)

        return () => {
            document.removeEventListener("mousedown", handleClickOutside, true)
            document.removeEventListener("keydown", handleEscapeKey)
        }
    }, [visible, isOpen])

    const handleToggle = () => setIsOpen((v) => !v)

    const handleItemClick = (item: any) => {
        const query = typeof item === "string" ? item : item?.prompt
        if (typeof query === "string" && query.trim().length > 0) {
            onSelect(query)
            setIsOpen(false)
        }
    }

    if (!visible) return null

    const hasNoPrompts = categories.every((category) => category.prompts.length === 0)

    const dropdownClasses =
        "flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg bg-chat-background p-2 transition-colors duration-200 ease-in-out hover:bg-chat-background-hover " +
        (isOpen ? "bg-chat-background-hover" : "")

    const menuClasses =
        "absolute bottom-full left-0 z-[1000] mb-1 max-h-[365px] min-h-[50px] w-[269px] overflow-y-auto rounded-[6px] border border-nav-border bg-chat-dropdown-background px-[2px] py-0 opacity-100 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] " +
        (isOpen ? "block animate-fadeInDropdown" : "hidden")

    const iconClasses =
        "absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] bg-chat-dropdown-icon transition-transform duration-300 ease-in-out " +
        (isOpen ? "rotate-180" : "")

    return (
        <div className="flex items-center gap-3">
            <div className="relative inline-block" ref={dropdownRef}>
                <div className={dropdownClasses} onClick={handleToggle}>
                    <div className="order-0 flex h-5 w-122 flex-none flex-grow-0 flex-col items-start gap-1 p-0">
                        <div className="order-0 h-5 w-122 flex-none flex-grow-0 self-stretch whitespace-nowrap font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text">
                            Suggested Prompts
                        </div>
                    </div>
                    <div className="relative order-1 h-6 w-6 flex-none flex-grow-0">
                        <div className={iconClasses} style={{ clipPath: "polygon(50% 100%, 0% 0%, 100% 0%)" }} />
                    </div>
                </div>

                <div className={menuClasses}>
                    {isLoading || hasNoPrompts ? (
                        <div className="px-2 py-2">
                            <LoadingSpinner message="Loading suggested prompts, waiting for server response" />
                        </div>
                    ) : (
                        <div className="px-2 py-2">
                            {categories.map((category, index) => (
                                <div key={`category-${index}`} className="px-2 py-2">
                                    {category.prompts.map((item: any, idx: number) => (
                                        <div
                                            key={`prompt-${index}-${idx}`}
                                            className="flex mx-0.5 my-0.5 flex-col min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-chat-dropdown-background px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-chat-background-hover gap-y-2"
                                            onClick={() => handleItemClick(item)}
                                        >
                                            <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text">
                                                {typeof item === "string" ? item : item?.prompt}
                                            </div>
                                            {typeof item !== "string" && item?.description && (
                                                <div className="w-full break-words font-cisco text-xs font-normal leading-4 tracking-[0%] text-chat-text opacity-70">
                                                    {item.description}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default DiscoveryPromptsDropdown
