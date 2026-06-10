/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import SendIcon from "@mui/icons-material/Send"
import { TextField } from "@mui/material"
import { Box, Button, Stack } from "@open-ui-kit/core"

import {
  CoffeePromptsDropdown,
  LogisticsPromptsDropdown,
  DiscoveryPromptsDropdown,
} from "./prompts"

const promptsDropdownSx = {
  flexShrink: 0,
  alignSelf: { xs: "stretch" as const, sm: "flex-end" as const },
}

interface ChatAreaComposerProps {
  showCoffeePrompts: boolean
  showLogisticsPrompts: boolean
  showDiscoveryPrompts: boolean
  pattern?: string
  onDropdownSelect: (query: string) => void
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
  onDropdownSelect,
  content,
  setContent,
  loading,
  onSend,
  onKeyDown,
}) => {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      alignItems={{ sm: "center" }}
      spacing={2}
      sx={{ width: "100%", maxWidth: 880 }}
    >
      {showCoffeePrompts ? (
        <Box sx={promptsDropdownSx}>
          <CoffeePromptsDropdown
            onSelect={onDropdownSelect}
            pattern={pattern}
          />
        </Box>
      ) : null}

      {showLogisticsPrompts ? (
        <Box sx={promptsDropdownSx}>
          <LogisticsPromptsDropdown onSelect={onDropdownSelect} />
        </Box>
      ) : null}

      {showDiscoveryPrompts ? (
        <Box sx={promptsDropdownSx}>
          <DiscoveryPromptsDropdown onSelect={onDropdownSelect} />
        </Box>
      ) : null}

      <TextField
        fullWidth
        margin="dense"
        variant="standard"
        label="Message to agents"
        placeholder="Type a prompt to interact with the agents"
        value={content}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setContent(e.target.value)
        }
        onKeyDown={onKeyDown}
        disabled={loading}
        slotProps={{
          inputLabel: {
            shrink: true,
          },
          input: {
            disableUnderline: true,
          },
        }}
        sx={{
          flex: 1,
          minWidth: 0,
          "& .MuiInputBase-input": {
            "&::placeholder": {
              opacity: 0.6,
            },
          },
        }}
      />
      <Button
        size="large"
        type="button"
        variant="primary"
        disabled={loading || !content.trim()}
        onClick={() => onSend()}
        endIcon={<SendIcon />}
        sx={{
          flexShrink: 0,
          alignSelf: { xs: "stretch", sm: "flex-end" },
        }}
      >
        Send
      </Button>
    </Stack>
  )
}

export default ChatAreaComposer
