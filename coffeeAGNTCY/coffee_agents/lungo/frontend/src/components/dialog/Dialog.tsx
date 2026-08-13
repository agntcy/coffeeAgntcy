/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Standard Lungo dialog shell: responsive OUK Dialog sizing, title bar, scroll body.
 */

import React from "react"
import { Dialog as OukDialog } from "@open-ui-kit/core"
import DialogContent from "@/components/dialog/DialogContent"
import DialogTitle from "@/components/dialog/DialogTitle"

interface DialogProps extends Omit<
  React.ComponentProps<typeof OukDialog>,
  "children" | "title" | "onClose" | "open"
> {
  open: boolean
  onClose: NonNullable<React.ComponentProps<typeof OukDialog>["onClose"]>
  title: React.ReactNode
  titleProps?: Omit<
    React.ComponentProps<typeof DialogTitle>,
    "onClose" | "children"
  >
  children: React.ReactNode
}

const Dialog: React.FC<DialogProps> = ({
  open,
  onClose,
  title,
  titleProps,
  children,
  maxWidth = "md",
  fullWidth = true,
  scroll = "paper",
  ...passThroughProps
}) => (
  <OukDialog
    open={open}
    onClose={onClose}
    maxWidth={maxWidth}
    fullWidth={fullWidth}
    scroll={scroll}
    {...passThroughProps}
  >
    <DialogTitle
      onClose={() => {
        onClose({}, "escapeKeyDown")
      }}
      {...titleProps}
    >
      {title}
    </DialogTitle>
    <DialogContent>{children}</DialogContent>
  </OukDialog>
)

export default Dialog
