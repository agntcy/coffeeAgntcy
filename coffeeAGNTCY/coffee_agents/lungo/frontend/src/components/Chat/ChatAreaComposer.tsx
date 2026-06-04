/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import SendIcon from "@mui/icons-material/Send"
import { TextField } from "@mui/material"
import { Button, Stack } from "@open-ui-kit/core"

import {
  CoffeePromptsDropdown,
  LogisticsPromptsDropdown,
  DiscoveryPromptsDropdown,
} from "./Prompts"

const promptStripSx = {
  position: "relative" as const,
  zIndex: 10,
  height: 36,
  width: "100%",
  maxWidth: 880,
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
    <>
      {showCoffeePrompts && (
        <Stack
          direction="row"
          alignItems="flex-start"
          spacing={1}
          sx={promptStripSx}
        >
          <CoffeePromptsDropdown
            onSelect={onDropdownSelect}
            pattern={pattern}
          />
        </Stack>
      )}

      {showLogisticsPrompts && (
        <Stack
          direction="row"
          alignItems="flex-start"
          spacing={1}
          sx={promptStripSx}
        >
          <LogisticsPromptsDropdown onSelect={onDropdownSelect} />
        </Stack>
      )}

      {showDiscoveryPrompts && (
        <Stack
          direction="row"
          alignItems="flex-start"
          spacing={1}
          sx={promptStripSx}
        >
          <DiscoveryPromptsDropdown onSelect={onDropdownSelect} />
        </Stack>
      )}

      <Stack
        direction={{ xs: "column", sm: "row" }}
        alignItems={{ sm: "center" }}
        spacing={2}
        sx={{ width: "100%", maxWidth: 880 }}
      >
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
    </>
  )
}

export default ChatAreaComposer
