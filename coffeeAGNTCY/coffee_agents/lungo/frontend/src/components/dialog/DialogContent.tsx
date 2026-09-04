/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Shared dialog body (OUK DialogContent with title/body bar + standard padding).
 * MUI `dividers` is omitted so the body/footer bar can be an OUK Divider in
 * DialogFooter instead of a bundled top+bottom pair.
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
  <OukDialogContent sx={dialogContentSx} {...contentProps}>
    {children}
  </OukDialogContent>
)

export default DialogContent
