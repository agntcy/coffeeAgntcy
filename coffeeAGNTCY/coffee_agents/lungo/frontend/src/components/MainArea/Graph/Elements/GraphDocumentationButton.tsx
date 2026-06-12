/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useCallback } from "react"
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined"
import { Box, IconButton, Tooltip } from "@open-ui-kit/core"
import { graphCanvasIconButtonSx } from "./graphCanvasIconButtonSx"

interface GraphDocumentationButtonProps {
  /** GitHub blob URL for the currently displayed workflow documentation. */
  documentationUrl?: string
  /** Accessible name fragment (e.g. workflow catalog name). */
  documentationLabel?: string
}

const GraphDocumentationButton: React.FC<GraphDocumentationButtonProps> = ({
  documentationUrl,
  documentationLabel,
}) => {
  const handleClick = useCallback(() => {
    if (documentationUrl === undefined) {
      return
    }
    window.open(documentationUrl, "_blank", "noopener,noreferrer")
  }, [documentationUrl])

  if (documentationUrl === undefined) {
    return null
  }

  const ariaLabel = documentationLabel
    ? `Open documentation for ${documentationLabel}`
    : "Open workflow documentation"

  return (
    <Box
      sx={{
        position: "absolute",
        top: (t) => t.spacing(5),
        right: (t) => t.spacing(2),
        zIndex: 5,
      }}
    >
      <Tooltip title="View documentation on GitHub" arrow>
        <Box component="span" sx={{ display: "inline-flex" }}>
          <IconButton
            size="medium"
            aria-label={ariaLabel}
            onClick={handleClick}
            sx={(t) => graphCanvasIconButtonSx(t)}
          >
            <DescriptionOutlinedIcon />
          </IconButton>
        </Box>
      </Tooltip>
    </Box>
  )
}

export default GraphDocumentationButton
