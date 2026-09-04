/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Standard Lungo dialog shell: responsive OUK Dialog sizing, title bar, scroll
 * body, optional footer (Divider + actions only when footer has children).
 */

import React from "react"
import { Dialog as OukDialog } from "@open-ui-kit/core"
import DialogContent from "@/components/dialog/DialogContent"
import DialogFooter from "@/components/dialog/DialogFooter"
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
  /** Action row. Omitted or empty children skip the footer divider. */
  footer?: React.ReactNode
  children: React.ReactNode
}

const Dialog: React.FC<DialogProps> = ({
  open,
  onClose,
  title,
  titleProps,
  footer,
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
    <DialogFooter>{footer}</DialogFooter>
  </OukDialog>
)

export default Dialog
