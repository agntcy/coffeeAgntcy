/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import {
  Box,
  Button,
  Icons,
  Menu,
  MenuItem,
  Typography,
} from "@open-ui-kit/core"
import { LoadingSpinner } from "@/components/loading/LoadingSpinner"
import { composerPrimaryButtonSx } from "@/utils/composerPrimaryButtonSx"
import { env } from "@/utils/env"

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  env.get("VITE_EXCHANGE_APP_API_URL") ?? DEFAULT_EXCHANGE_APP_API_URL

interface CoffeeGraderDropdownProps {
  visible: boolean
  onSelect: (query: string) => void
}

const CoffeeGraderDropdown: React.FC<CoffeeGraderDropdownProps> = ({
  visible,
  onSelect,
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [dropdownItems, setDropdownItems] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const open = Boolean(anchorEl)

  useEffect(() => {
    const controller = new AbortController()
    let retryTimeoutId: ReturnType<typeof setTimeout> | null = null
    const MAX_RETRY_DELAY = 5000

    const fetchPrompts = async (retryCount = 0) => {
      try {
        setIsLoading(true)
        const res = await fetch(`${EXCHANGE_APP_API_URL}/suggested-prompts`, {
          cache: "no-cache",
          signal: controller.signal,
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (
          Array.isArray(data) &&
          data.every((p: unknown) => typeof p === "string")
        ) {
          setDropdownItems(data as string[])

          if (data.length === 0) {
            const delay = Math.min(
              5000 * Math.pow(2, retryCount),
              MAX_RETRY_DELAY,
            )
            retryTimeoutId = setTimeout(
              () => fetchPrompts(retryCount + 1),
              delay,
            )
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") {
          console.warn("Failed to load prompts from API.", err)
          const delay = Math.min(
            5000 * Math.pow(2, retryCount),
            MAX_RETRY_DELAY,
          )
          retryTimeoutId = setTimeout(() => fetchPrompts(retryCount + 1), delay)
        }
      } finally {
        setIsLoading(false)
      }
    }

    void fetchPrompts()

    return () => {
      controller.abort()
      if (retryTimeoutId) clearTimeout(retryTimeoutId)
    }
  }, [])

  const handleOpen = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      setAnchorEl(event.currentTarget)
      event.stopPropagation()
    },
    [],
  )

  const handleClose = useCallback(() => {
    setAnchorEl(null)
  }, [])

  const handleItemClick = useCallback(
    (item: string) => {
      onSelect(item)
      setAnchorEl(null)
    },
    [onSelect],
  )

  if (!visible) {
    return null
  }

  const hasNoPrompts = dropdownItems.length === 0

  return (
    <>
      <Button
        variant="primary"
        size="medium"
        aria-haspopup="menu"
        aria-expanded={open ? "true" : undefined}
        onClick={handleOpen}
        sx={(theme) => ({
          ...theme.typography.body1,
          ...composerPrimaryButtonSx(theme),
        })}
        endIcon={
          <Icons.KeyboardArrowDown
            aria-hidden
            sx={{
              transition: (theme) =>
                theme.transitions.create("transform", {
                  duration: theme.transitions.duration.shortest,
                }),
              transform: open ? "rotate(180deg)" : "rotate(0deg)",
            }}
          />
        }
      >
        Suggested Prompts
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: "top", horizontal: "left" }}
        transformOrigin={{ vertical: "bottom", horizontal: "left" }}
        slotProps={{
          paper: {
            sx: {
              maxHeight: 365,
              maxWidth: 480,
            },
          },
        }}
      >
        {isLoading || hasNoPrompts ? (
          <Box sx={{ p: 1 }}>
            <LoadingSpinner message="Loading suggested prompts from exchange server" />
          </Box>
        ) : (
          dropdownItems.map((item, index) => (
            <MenuItem
              key={index}
              onClick={() => handleItemClick(item)}
              sx={{ whiteSpace: "normal", alignItems: "flex-start", py: 1 }}
            >
              <Typography variant="body1" sx={{ wordBreak: "break-word" }}>
                {item}
              </Typography>
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  )
}

export default CoffeeGraderDropdown
