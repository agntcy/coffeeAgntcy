/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Spinner } from "@open-ui-kit/core"

interface LoadingSpinnerProps {
  message?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message }) => {
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-4">
      <Spinner size={24} thickness={4} />
      {message && (
        <div className="text-center font-cisco text-[10px] text-chat-text opacity-60">
          {message}
        </div>
      )}
    </div>
  )
}

export default LoadingSpinner
