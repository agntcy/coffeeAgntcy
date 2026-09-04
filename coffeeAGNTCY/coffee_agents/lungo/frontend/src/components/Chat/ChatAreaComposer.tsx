/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import SendIcon from "@mui/icons-material/Send"
import { Box, Button, InputField, Stack } from "@open-ui-kit/core"

import { iconGlyphFillSx } from "@/utils/iconGlyphFill"
import { composerPrimaryButtonSx } from "@/utils/composerPrimaryButtonSx"

import type { HttpRequestTarget } from "@/urls"

import {
  chatComposerNarrowContainerQuery,
  CHAT_COMPOSER_STACKED_GAP_PX,
} from "./chatComposerLayout"
import { SuggestedPromptsDropdown } from "./prompts"

/** Matches OUK `Button` `size="medium"` with compact `body1` typography (7 + 20 + 7 = 34px). */
const COMPOSER_CONTROL_HEIGHT_PX = 34

const promptsDropdownSx = {
  flexShrink: 0,
  alignSelf: "flex-end" as const,
  [chatComposerNarrowContainerQuery]: {
    alignSelf: "stretch",
  },
}

interface ChatAreaComposerProps {
  suggestedPromptsRequest?: HttpRequestTarget | null
  onSuggestedPromptSelect: (query: string) => void
  content: string
  setContent: (value: string) => void
  loading: boolean
  onSend: () => void
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

const ChatAreaComposer: React.FC<ChatAreaComposerProps> = ({
  suggestedPromptsRequest,
  onSuggestedPromptSelect,
  content,
  setContent,
  loading,
  onSend,
  onKeyDown,
}) => {
  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={2}
      sx={{
        width: "100%",
        [chatComposerNarrowContainerQuery]: {
          flexDirection: "column",
          alignItems: "stretch",
          gap: `${CHAT_COMPOSER_STACKED_GAP_PX}px`,
          "& > :not(style) ~ :not(style)": {
            margin: 0,
          },
        },
      }}
    >
      {suggestedPromptsRequest ? (
        <Box sx={promptsDropdownSx}>
          <SuggestedPromptsDropdown
            promptsRequest={suggestedPromptsRequest}
            onSelect={onSuggestedPromptSelect}
            sx={(theme) => ({
              ...theme.typography.body1,
              ...composerPrimaryButtonSx(theme),
            })}
          />
        </Box>
      ) : null}

      <InputField
        fullWidth
        size="small"
        placeholder="Type a prompt to interact with the agents"
        value={content}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setContent(e.target.value)
        }
        onKeyDown={onKeyDown}
        disabled={loading}
        slotProps={{
          htmlInput: {
            "aria-label": "Message to agents",
          },
        }}
        sx={(theme) => ({
          "& .MuiInput-root.MuiInputBase-sizeSmall": {
            marginTop: 0,
            height: COMPOSER_CONTROL_HEIGHT_PX,
            minHeight: COMPOSER_CONTROL_HEIGHT_PX,
            borderColor: "transparent",

            "&:has(.MuiInput-input:not(:placeholder-shown))": {
              borderColor: theme.palette.vars.interactiveTertiaryDefault,
            },
            "&:has(.MuiInput-input:not(:placeholder-shown)):hover": {
              borderColor: theme.palette.vars.interactiveTertiaryHover,
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
          alignSelf: "flex-end",
          [chatComposerNarrowContainerQuery]: {
            alignSelf: "stretch",
          },
          ...theme.typography.body1,
          ...composerPrimaryButtonSx(theme),
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
