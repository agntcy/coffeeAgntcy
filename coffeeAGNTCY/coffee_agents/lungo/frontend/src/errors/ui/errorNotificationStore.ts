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

const MAX_ERROR_NOTIFICATIONS = 5

function notificationDedupeKey(input: {
  severity: ErrorNotificationSeverity
  title: string
  message: string
  source?: string
}): string {
  return JSON.stringify({
    severity: input.severity,
    title: input.title,
    message: input.message,
    source: input.source ?? "",
  })
}

type ErrorNotificationState = {
  notifications: ErrorNotification[]
  pushError: (input: PushErrorInput) => string
  dismissError: (id: string) => void
  clearAll: () => void
}

export const useErrorNotificationStore = create<ErrorNotificationState>(
  (set, get) => ({
    notifications: [],
    pushError: (input) => {
      const severity = input.severity ?? "error"
      const key = notificationDedupeKey({
        severity,
        title: input.title,
        message: input.message,
        source: input.source,
      })

      const existing = get().notifications.find(
        (notification) =>
          notificationDedupeKey({
            severity: notification.severity,
            title: notification.title,
            message: notification.message,
            source: notification.source,
          }) === key,
      )
      if (existing) {
        return existing.id
      }

      const id = input.id ?? uuidv4()
      const notification: ErrorNotification = {
        id,
        severity,
        title: input.title,
        message: input.message,
        source: input.source,
      }

      set((state) => {
        const next = [...state.notifications, notification]
        return {
          notifications:
            next.length > MAX_ERROR_NOTIFICATIONS
              ? next.slice(-MAX_ERROR_NOTIFICATIONS)
              : next,
        }
      })

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
