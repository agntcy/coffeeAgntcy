/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react"
import ReactMarkdown from "react-markdown"
import rehypeSanitize from "rehype-sanitize"
import { Box } from "@open-ui-kit/core"
import MermaidBlock from "./MermaidBlock"

interface PatternDocMarkdownProps {
  markdown: string
  className?: string
}

const isMermaidCodeBlock = (className: string | undefined): boolean =>
  typeof className === "string" &&
  className.split(/\s+/).includes("language-mermaid")

const PatternDocMarkdown: React.FC<PatternDocMarkdownProps> = ({
  markdown,
  className,
}) => {
  return (
    <Box className={className}>
      <ReactMarkdown
        rehypePlugins={[rehypeSanitize]}
        components={{
          code({ className: codeClass, children, ...rest }) {
            if (isMermaidCodeBlock(codeClass)) {
              const chart = String(children ?? "").replace(/\n$/, "")
              return <MermaidBlock chart={chart} />
            }
            return (
              <code className={codeClass} {...rest}>
                {children}
              </code>
            )
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </Box>
  )
}

export default PatternDocMarkdown
