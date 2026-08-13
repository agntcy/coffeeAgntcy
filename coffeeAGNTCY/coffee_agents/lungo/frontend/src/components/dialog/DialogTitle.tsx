/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared dialog title bar (OUK DialogTitle + top-right close button).
 */

import React from "react"
import { DialogTitle as OukDialogTitle } from "@open-ui-kit/core"
import DialogCloseButton from "@/components/dialog/DialogCloseButton"
import { dialogTitleSx } from "@/components/dialog/dialogTitleSx"

interface DialogTitleProps extends Omit<
  React.ComponentProps<typeof OukDialogTitle>,
  "sx"
> {
  onClose: () => void
}

const DialogTitle: React.FC<DialogTitleProps> = ({
  onClose,
  children,
  ...titleProps
}) => (
  <OukDialogTitle sx={dialogTitleSx} {...titleProps}>
    {children}
    <DialogCloseButton onClose={onClose} />
  </OukDialogTitle>
)

export default DialogTitle
