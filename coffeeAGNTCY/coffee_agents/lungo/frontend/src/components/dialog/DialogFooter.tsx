/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Dialog action row. Draws an OUK Divider above DialogActions only when the
 * footer has real children (null / false / empty fragments do not count).
 */

import React from "react"
import {
  Box,
  DialogActions as OukDialogActions,
  Divider,
} from "@open-ui-kit/core"

interface DialogFooterProps {
  children?: React.ReactNode
}

const hasFooterChildren = (children: React.ReactNode): boolean =>
  React.Children.toArray(children).some((child) => {
    if (typeof child === "string") {
      return child.trim().length > 0
    }
    if (!React.isValidElement(child)) {
      return true
    }
    if (child.type === React.Fragment) {
      return hasFooterChildren(
        (child.props as { children?: React.ReactNode }).children,
      )
    }
    return true
  })

const DialogFooter: React.FC<DialogFooterProps> = ({ children }) => {
  if (!hasFooterChildren(children)) {
    return null
  }

  return (
    <Box sx={{ flexShrink: 0 }}>
      <Divider />
      <OukDialogActions>{children}</OukDialogActions>
    </Box>
  )
}

export default DialogFooter
