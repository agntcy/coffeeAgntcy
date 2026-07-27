/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Banner, Box, type StatusBanner } from "@open-ui-kit/core"
import {
  type ErrorNotificationSeverity,
  useErrorNotificationStore,
} from "./errorNotificationStore"

const severityToBannerStatus = (
  severity: ErrorNotificationSeverity,
): StatusBanner => {
  switch (severity) {
    case "error":
      return "negative"
    case "warning":
      return "warning"
    case "info":
      return "info"
  }
}

const ErrorNotifications = () => {
  const notifications = useErrorNotificationStore(
    (state) => state.notifications,
  )
  const dismissError = useErrorNotificationStore((state) => state.dismissError)

  if (notifications.length === 0) {
    return null
  }

  return (
    <Box
      role="region"
      aria-label="Application notifications"
      sx={{
        position: "fixed",
        top: 16,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 1400,
        width: "min(100% - 32px, 560px)",
        display: "flex",
        flexDirection: "column",
        gap: 1,
        pointerEvents: "none",
        "& > *": {
          pointerEvents: "auto",
        },
      }}
    >
      {notifications.map((notification) => (
        <Banner
          key={notification.id}
          role="alert"
          status={severityToBannerStatus(notification.severity)}
          showCloseButton
          onClose={() => dismissError(notification.id)}
          sx={{ width: "100%" }}
          text={
            <>
              <strong>{notification.title}</strong>
              <br />
              {notification.message}
            </>
          }
        />
      ))}
    </Box>
  )
}

export default ErrorNotifications
