/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { LoaderCircle } from "lucide-react"

interface LoadingSpinnerProps {
    message?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message }) => {
    return (
        <div className="flex flex-col items-center justify-center gap-2 p-4">
            <LoaderCircle className="h-6 w-6 animate-spin text-chat-text" />
            {message && (
                <div className="text-center font-cisco text-[10px] text-chat-text opacity-60">
                    {message}
                </div>
            )}
        </div>
    )
}

export default LoadingSpinner