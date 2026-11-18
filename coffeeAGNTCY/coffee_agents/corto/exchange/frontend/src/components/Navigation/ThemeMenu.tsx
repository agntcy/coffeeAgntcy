/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Light, dark, or system. System follows the OS color scheme.
 */

import React, { useId, useState } from "react"
import Tonality from "@mui/icons-material/Tonality"
import {
  Box,
  IconButton,
  Icons,
  Menu,
  MenuItem,
  Tooltip,
} from "@open-ui-kit/core"

import { useAppThemeMode } from "@/hooks/useAppThemeMode"
import type { StoredThemeMode } from "@/utils/themeStorage"
import { navigationHeaderIconButtonSx } from "./navigationHeaderSx"

const choiceIconSx = { width: 20, height: 20, fontSize: 20 }

const CHOICES: {
  value: StoredThemeMode
  label: string
  Icon: React.ElementType
}[] = [
  { value: "light", label: "Light", Icon: Icons.LightMode },
  { value: "dark", label: "Dark", Icon: Icons.DarkMode },
  { value: "system", label: "System", Icon: Tonality },
]

const ThemeMenu: React.FC = () => {
  const menuId = useId()
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const { preference, setThemePreference } = useAppThemeMode()
  const open = Boolean(anchorEl)
  const selected = preference ?? "system"
  const SelectedIcon =
    CHOICES.find((choice) => choice.value === selected)?.Icon ?? Tonality

  return (
    <>
      <Tooltip title="Theme">
        <IconButton
          aria-label="Choose theme"
          aria-controls={open ? menuId : undefined}
          aria-haspopup="menu"
          aria-expanded={open ? "true" : undefined}
          onClick={(event) => setAnchorEl(event.currentTarget)}
          sx={(theme) => navigationHeaderIconButtonSx(theme)}
        >
          <SelectedIcon aria-hidden sx={choiceIconSx} />
        </IconButton>
      </Tooltip>
      <Menu
        id={menuId}
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
      >
        {CHOICES.map((choice) => {
          const isSelected = selected === choice.value
          return (
            <MenuItem
              key={choice.value}
              selected={isSelected}
              role="menuitemradio"
              aria-checked={isSelected}
              onClick={() => {
                setThemePreference(choice.value)
                setAnchorEl(null)
              }}
            >
              <Box
                component="span"
                sx={{ display: "inline-flex", alignItems: "center" }}
              >
                <choice.Icon aria-hidden sx={choiceIconSx} />
                <Box component="span" sx={{ ml: 2 }}>
                  {choice.label}
                </Box>
              </Box>
            </MenuItem>
          )
        })}
      </Menu>
    </>
  )
}

export default ThemeMenu
