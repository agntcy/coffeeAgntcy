/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import SendIcon from "@mui/icons-material/Send"
import { TextField } from "@mui/material"
import { Button, Stack } from "@open-ui-kit/core"

import CoffeePromptsDropdown from "./Prompts/CoffeePromptsDropdown"
import LogisticsPromptsDropdown from "./Prompts/LogisticsPromptsDropdown"
import DiscoveryPromptsDropdown from "./Prompts/DiscoveryPromptsDropdown"

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
            visible={true}
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
          <LogisticsPromptsDropdown
            visible={true}
            onSelect={onDropdownSelect}
          />
        </Stack>
      )}

      {showDiscoveryPrompts && (
        <Stack
          direction="row"
          alignItems="flex-start"
          spacing={1}
          sx={promptStripSx}
        >
          <DiscoveryPromptsDropdown
            visible={true}
            onSelect={onDropdownSelect}
          />
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
          type="button"
          variant="primary"
          disabled={loading || !content.trim()}
          onClick={() => onSend()}
          endIcon={<SendIcon />}
          sx={{
            flexShrink: 0,
            alignSelf: { xs: "stretch", sm: "center" },
          }}
        >
          Send
        </Button>
      </Stack>
    </>
  )
}

export default ChatAreaComposer
