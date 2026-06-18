/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import SendIcon from "@mui/icons-material/Send"
import { TextField } from "@mui/material"
import { Box, Button, Stack } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"

import {
  resolveSuggestedPromptsSource,
  SuggestedPromptsDropdown,
} from "./prompts"

/** Matches OUK `Button` `size="medium"` in the compact shell (see ChatHeader icon buttons). */
const COMPOSER_CONTROL_HEIGHT_PX = 32

const promptsDropdownSx = {
  flexShrink: 0,
  alignSelf: { xs: "stretch" as const, sm: "flex-end" as const },
}

interface ChatAreaComposerProps {
  showCoffeePrompts: boolean
  showLogisticsPrompts: boolean
  showDiscoveryPrompts: boolean
  pattern?: string
  onSuggestedPromptSelect: (query: string) => void
  content: string
  setContent: (value: string) => void
  loading: boolean
  onSend: () => void
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

const ChatAreaComposer: React.FC<ChatAreaComposerProps> = ({
  showCoffeePrompts,
  showLogisticsPrompts,
  showDiscoveryPrompts,
  pattern,
  onSuggestedPromptSelect,
  content,
  setContent,
  loading,
  onSend,
  onKeyDown,
}) => {
  const promptsSource = resolveSuggestedPromptsSource({
    showCoffeePrompts,
    showLogisticsPrompts,
    showDiscoveryPrompts,
  })

  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      alignItems={{ xs: "stretch", sm: "flex-end" }}
      spacing={2}
      sx={{ width: "100%", maxWidth: 1100, mx: "auto" }}
    >
      {promptsSource ? (
        <Box sx={promptsDropdownSx}>
          <SuggestedPromptsDropdown
            source={promptsSource}
            pattern={pattern}
            onSelect={onSuggestedPromptSelect}
          />
        </Box>
      ) : null}

      <TextField
        fullWidth
        margin="none"
        variant="standard"
        placeholder="Type a prompt to interact with the agents"
        value={content}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setContent(e.target.value)
        }
        onKeyDown={onKeyDown}
        disabled={loading}
        slotProps={{
          input: {
            disableUnderline: true,
          },
          htmlInput: {
            "aria-label": "Message to agents",
            sx: {
              minWidth: 0,
            },
          },
        }}
        sx={(theme) => ({
          flex: 1,
          minWidth: 0,
          maxWidth: "100%",
          my: 0,
          "& .MuiInputBase-root": {
            width: "100%",
            minWidth: 0,
            marginTop: 0,
            height: COMPOSER_CONTROL_HEIGHT_PX,
            minHeight: COMPOSER_CONTROL_HEIGHT_PX,
            boxSizing: "border-box",
            alignItems: "center",
          },
          "& .MuiInputBase-input": {
            ...theme.typography.body1,
            width: "100%",
            minWidth: 0,
            boxSizing: "border-box",
            height: theme.typography.body1.lineHeight,
            padding: 0,
            "&::placeholder": {
              opacity: 0.6,
            },
          },
        })}
      />
      <Button
        size="medium"
        type="button"
        variant="primary"
        disabled={loading || !content.trim()}
        onClick={() => onSend()}
        endIcon={<SendIcon />}
        sx={(theme) => ({
          flexShrink: 0,
          alignSelf: { xs: "stretch", sm: "flex-end" },
          "& .MuiButton-endIcon": iconGlyphFillSx(
            theme.palette.vars.baseTextInverse,
            { important: true },
          ),
        })}
      >
        Send
      </Button>
    </Stack>
  )
}

export default ChatAreaComposer
