/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState } from "react"
import Close from "@mui/icons-material/Close"
import InfoOutlined from "@mui/icons-material/InfoOutlined"
import { IconButton } from "@open-ui-kit/core"
import ReactMarkdown from "react-markdown"
import rehypeSanitize from "rehype-sanitize"
import { stripHtml } from "@/utils/const"

/**
 * infoContent must come from trusted app/constants only.
 * If it ever comes from API or user input, sanitize first or pass plain text.
 * rehypeSanitize is used as defense-in-depth to strip unsafe HTML.
 */
interface InfoButtonProps {
  infoContent: string
  className?: string
  iconSize?: number
}

const InfoButton: React.FC<InfoButtonProps> = ({
  infoContent,
  className,
  iconSize = 16,
}) => {
  const [showInfo, setShowInfo] = useState(false)

  const handleToggle = () => setShowInfo((prev) => !prev)
  const handleClose = () => setShowInfo(false)

  return (
    <div className={`relative ${className || ""}`}>
      {showInfo && (
        <div
          className="absolute z-[1100] flex items-center gap-2 rounded p-2 shadow"
          style={{
            backgroundColor: "var(--info-bg)",
            border: "1px solid var(--info-border)",
          }}
        >
          <div className="relative w-72 max-w-md">
            <IconButton
              onClick={handleClose}
              aria-label="Close"
              size="small"
              sx={{
                position: "absolute",
                left: -17.5,
                top: -17.5,
                zIndex: 1200,
                width: 20,
                height: 20,
                p: 0,
              }}
            >
              <Close sx={{ fontSize: 12 }} />
            </IconButton>

            <div className="text-sm" style={{ color: "var(--info-text)" }}>
              <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                {stripHtml(infoContent)}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      <IconButton
        onClick={handleToggle}
        aria-label="More information"
        size="small"
        sx={{
          position: "absolute",
          zIndex: 1000,
          px: 0.25,
          py: 0.25,
        }}
      >
        <InfoOutlined sx={{ fontSize: iconSize }} />
      </IconButton>
    </div>
  )
}

export default InfoButton
