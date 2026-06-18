/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Render an assistant chat response as markdown.
 *
 * - remark-gfm: autolink bare URLs, tables, strikethrough, task lists.
 * - remark-breaks: single newlines become <br> so plain-text responses keep
 *   their line breaks (markdown would otherwise collapse them to spaces).
 * - rehype-sanitize: defense-in-depth against HTML injection from LLM output.
 *
 * Outer margins are collapsed so a single plain-text paragraph renders the
 * same as the previous plain-text path.
 */

import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkBreaks from "remark-breaks"
import rehypeSanitize from "rehype-sanitize"
import { Box } from "@open-ui-kit/core"

interface ChatMarkdownProps {
  content: string
}

const ChatMarkdown: React.FC<ChatMarkdownProps> = ({ content }) => {
  return (
    <Box
      sx={{
        "& > *:first-of-type": { mt: 0 },
        "& > *:last-child": { mb: 0 },
        "& p": { my: 0.5 },
        "& ul, & ol": { my: 0.5, pl: 3 },
        "& li": { my: 0.25 },
        "& h1, & h2, & h3, & h4": { my: 0.75, fontWeight: 600 },
        "& a": { color: "primary.main", textDecoration: "underline" },
        "& code": {
          fontFamily: "monospace",
          fontSize: "0.85em",
          px: 0.5,
          py: 0.125,
          borderRadius: 0.5,
          bgcolor: "action.hover",
        },
        "& pre": {
          my: 0.5,
          p: 1.5,
          borderRadius: 1,
          overflowX: "auto",
          bgcolor: "action.hover",
        },
        "& pre code": { p: 0, bgcolor: "transparent" },
        "& table": { borderCollapse: "collapse", my: 0.5 },
        "& th, & td": { border: 1, borderColor: "divider", px: 1, py: 0.5 },
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          a({ children, ...rest }) {
            return (
              <a {...rest} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  )
}

export default ChatMarkdown
