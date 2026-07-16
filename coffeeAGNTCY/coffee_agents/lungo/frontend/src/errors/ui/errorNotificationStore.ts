/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { create } from "zustand"
import { v4 as uuidv4 } from "uuid"

export type ErrorNotificationSeverity = "error" | "warning" | "info"

export type ErrorNotification = {
  id: string
  severity: ErrorNotificationSeverity
  title: string
  message: string
  source?: string
}

export type PushErrorInput = {
  id?: string
  severity?: ErrorNotificationSeverity
  title: string
  message: string
  source?: string
}

type ErrorNotificationState = {
  notifications: ErrorNotification[]
  pushError: (input: PushErrorInput) => string
  dismissError: (id: string) => void
  clearAll: () => void
}

export const useErrorNotificationStore = create<ErrorNotificationState>(
  (set) => ({
    notifications: [],
    pushError: (input) => {
      const id = input.id ?? uuidv4()
      const notification: ErrorNotification = {
        id,
        severity: input.severity ?? "error",
        title: input.title,
        message: input.message,
        source: input.source,
      }

      set((state) => ({
        notifications: [...state.notifications, notification],
      }))

      return id
    },
    dismissError: (id) => {
      set((state) => ({
        notifications: state.notifications.filter(
          (notification) => notification.id !== id,
        ),
      }))
    },
    clearAll: () => set({ notifications: [] }),
  }),
)
