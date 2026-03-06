/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"
import { env } from "@/utils/env"
import { stripHtml } from "@/utils/const"
import { logger } from "@/utils/logger"
import LoadingSpinner from "./LoadingSpinner"
import { PromptCategory } from "./PromptTypes"

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  env.get("VITE_EXCHANGE_APP_API_URL") || DEFAULT_EXCHANGE_APP_API_URL

interface CoffeePromptsDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
  pattern?: string
}

const CoffeePromptsDropdown: React.FC<CoffeePromptsDropdownProps> = ({
  visible,
  onSelect,
  pattern,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [categories, setCategories] = useState<PromptCategory[]>([])
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Fetch prompts on mount or pattern change
  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    const MAX_RETRY_DELAY = 5000 // 5 seconds max

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const isStreamingPattern = pattern === "publish_subscribe_streaming"
        const url = isStreamingPattern
          ? `${EXCHANGE_APP_API_URL}/suggested-prompts?pattern=streaming`
          : `${EXCHANGE_APP_API_URL}/suggested-prompts`

        const res = await fetch(url, {
          cache: "no-cache",
          signal: controller.signal,
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data: unknown = await res.json()

        logger.debug("Fetched prompts data:", data)

        const categories =
          data !== null && typeof data === "object" && !Array.isArray(data)
            ? Object.entries(data as Record<string, unknown>).map(
                ([key, value]) => ({
                  name: key,
                  prompts: Array.isArray(value) ? value : [],
                }),
              )
            : []
        setCategories(categories)

        // Retry if all categories are empty
        if (categories.every((category) => category.prompts.length === 0)) {
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }

        setIsLoading(false) // Only set to false after successful fetch and processing
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          logger.warn("Failed to load prompts from API.", err)
          // Retry on error with exponential backoff
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }
      }
    }

    fetchPrompts()

    return () => {
      controller.abort()
      if (retryTimeoutId) clearTimeout(retryTimeoutId)
    }
  }, [pattern])

  // Handle outside clicks and escape key
  useEffect(() => {
    if (!visible || !isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
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

  const handleToggle = () => setIsOpen(!isOpen)

  const handleItemClick = (item: string) => {
    onSelect(item)
    setIsOpen(false)
  }

  if (!visible) return null

  const dropdownClasses = `flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg bg-chat-background p-2 transition-colors duration-200 ease-in-out hover:bg-chat-background-hover ${
    isOpen ? "bg-chat-background-hover" : ""
  }`

  const hasNoPrompts = categories.every(
    (category) => category.prompts.length === 0,
  )

  const menuClasses = `absolute bottom-full left-0 z-[1000] mb-1 max-h-[365px] min-h-[50px] w-[269px] overflow-y-auto rounded-[6px] border border-nav-border bg-chat-dropdown-background px-[2px] py-0 opacity-100 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${
    isOpen ? "block animate-fadeInDropdown" : "hidden"
  }`

  const iconClasses = `absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] bg-chat-dropdown-icon transition-transform duration-300 ease-in-out ${
    isOpen ? "rotate-180" : ""
  }`

  return (
    <div className="flex items-center gap-3">
      <div className="relative inline-block" ref={dropdownRef}>
        <div className={dropdownClasses} onClick={handleToggle}>
          <div className="order-0 flex h-5 w-122 flex-none flex-grow-0 flex-col items-start gap-1 p-0">
            <div className="order-0 h-5 w-122 flex-none flex-grow-0 self-stretch whitespace-nowrap font-cisco text-sm font-normal leading-5 text-chat-text">
              Suggested Prompts
            </div>
          </div>
          <div className="relative order-1 h-6 w-6 flex-none flex-grow-0">
            <div
              className={iconClasses}
              style={{ clipPath: "polygon(50% 100%, 0% 0%, 100% 0%)" }}
            />
          </div>
        </div>

        <div className={menuClasses}>
          {isLoading || hasNoPrompts ? (
            <LoadingSpinner message="Loading suggested prompts, waiting for server response" />
          ) : (
            categories.map((category, index) => (
              <div key={`category-${index}`} className="px-2 py-2">
                {(category.name === "buyer" ||
                  category.name === "purchaser") && (
                  <div className="mb-2 h-[36px] w-[265px] gap-2 bg-chat-dropdown-background pb-2 pl-[10px] pr-[10px] pt-2 font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text opacity-60">
                    {category.name.toUpperCase()}
                  </div>
                )}
                {category.prompts.map((item, idx) => (
                  <div
                    key={`prompt-${index}-${idx}`}
                    className={`mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer flex-col items-center gap-y-1.5 bg-chat-dropdown-background px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-chat-background-hover ${
                      category.name === "buyer" || category.name === "purchaser"
                        ? "border-t border-gray-400 border-opacity-40"
                        : ""
                    }`}
                    onClick={() => handleItemClick(item.prompt)}
                  >
                    <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text">
                      {stripHtml(item.prompt ?? "")}
                    </div>
                    {item.description && (
                      <div className="w-full break-words font-cisco text-xs font-normal leading-4 tracking-[0%] text-chat-text opacity-70">
                        {stripHtml(item.description)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default CoffeePromptsDropdown
