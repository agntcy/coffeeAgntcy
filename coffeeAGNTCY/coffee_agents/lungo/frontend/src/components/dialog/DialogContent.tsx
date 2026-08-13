/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared dialog body (OUK DialogContent with dividers + standard padding).
 */

import React from "react"
import { DialogContent as OukDialogContent } from "@open-ui-kit/core"
import { dialogContentSx } from "@/components/dialog/dialogContentSx"

interface DialogContentProps extends Omit<
  React.ComponentProps<typeof OukDialogContent>,
  "dividers" | "sx"
> {
  children: React.ReactNode
}

const DialogContent: React.FC<DialogContentProps> = ({
  children,
  ...contentProps
}) => (
  <OukDialogContent dividers sx={dialogContentSx} {...contentProps}>
    {children}
  </OukDialogContent>
)

export default DialogContent
