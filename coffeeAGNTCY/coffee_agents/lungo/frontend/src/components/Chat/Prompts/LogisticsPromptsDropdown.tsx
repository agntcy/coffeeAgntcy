/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useRef, useEffect } from "react"
import LoadingSpinner from "./LoadingSpinner"

const DEFAULT_LOGISTICS_APP_API_URL = "http://127.0.0.1:9090"
const LOGISTICS_APP_API_URL =
  import.meta.env.VITE_LOGISTICS_APP_API_URL || DEFAULT_LOGISTICS_APP_API_URL

interface LogisticsPromptsDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const LogisticsPromptsDropdown: React.FC<LogisticsPromptsDropdownProps> = ({
                                                                             visible,
                                                                             onSelect,
                                                                           }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [logisticsPrompts, setLogisticsPrompts] = useState<string[]>([])
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch prompts on mount
  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: NodeJS.Timeout | null = null
    const MAX_RETRY_DELAY = 5000 // 5 seconds max

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const res = await fetch(`${LOGISTICS_APP_API_URL}/suggested-prompts`, {
          cache: "no-cache",
          signal: controller.signal,
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data: unknown = await res.json()

        if (Array.isArray(data)) {
          const prompts = data.filter((p): p is string => typeof p === "string")
          setLogisticsPrompts(prompts)

          // Retry if no prompts returned
          if (prompts.length === 0) {
            const delay = Math.min(5000 * Math.pow(2, retryCount), MAX_RETRY_DELAY)
            retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          console.warn("Failed to load logistics prompts from API.", err)
          // Retry on error with exponential backoff
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

  // Handle outside clicks and escape key
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

  const handleToggle = () => setIsOpen(!isOpen)

  const handleItemClick = (prompt: string) => {
    onSelect(prompt)
    setIsOpen(false)
  }

  if (!visible) return null

  const dropdownClasses = `flex h-9 w-166 cursor-pointer flex-row items-center gap-1 rounded-lg bg-chat-background p-2 transition-colors duration-200 ease-in-out hover:bg-chat-background-hover ${isOpen ? "bg-chat-background-hover" : ""}`

  const menuClasses = `absolute bottom-full left-0 z-[1000] mb-1 w-269 overflow-y-auto rounded-[6px] border border-nav-border bg-chat-dropdown-background px-[2px] py-0 opacity-100 shadow-[0px_2px_5px_0px_rgba(0,0,0,0.05)] ${isOpen ? "block animate-fadeInDropdown" : "hidden"}`

  const iconClasses = `absolute bottom-[36.35%] left-[26.77%] right-[26.77%] top-[36.35%] bg-chat-dropdown-icon transition-transform duration-300 ease-in-out ${isOpen ? "rotate-180" : ""}`

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
            <div className="px-2 py-2">
              {isLoading ? (
                  <div className="flex items-center justify-center p-4">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-chat-text border-t-transparent" />
                  </div>
              ) : logisticsPrompts.length === 0 ? (
                  <LoadingSpinner
                      message={"Loading suggested prompts, waiting for logistics server response"}
                  />
              ) : (
                  logisticsPrompts.map((item, index) => (
                      <div
                          key={`prompt-${index}`}
                          className="mx-0.5 my-0.5 flex min-h-10 w-[calc(100%-4px)] cursor-pointer items-center rounded bg-chat-dropdown-background px-2 py-[6px] transition-colors duration-200 ease-in-out hover:bg-chat-background-hover"
                          onClick={() => handleItemClick(item)}
                      >
                        <div className="w-full break-words font-cisco text-sm font-normal leading-5 tracking-[0%] text-chat-text">
                          {item}
                        </div>
                      </div>
                  ))
              )}
            </div>
          </div>
        </div>
      </div>
  )
}

export default LogisticsPromptsDropdown
