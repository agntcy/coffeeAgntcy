/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared close control for Lungo dialogs (top-right of title bar).
 */

import React from "react"
import Close from "@mui/icons-material/Close"
import { IconButton } from "@open-ui-kit/core"
import { dialogCloseIconButtonSx } from "@/components/dialog/dialogTitleSx"

interface DialogCloseButtonProps {
  onClose: () => void
}

const DialogCloseButton: React.FC<DialogCloseButtonProps> = ({ onClose }) => (
  <IconButton onClick={onClose} aria-label="Close" sx={dialogCloseIconButtonSx}>
    <Close />
  </IconButton>
)

export default DialogCloseButton
