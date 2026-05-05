/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useState } from "react"
import Person from "@mui/icons-material/Person"
import SmartToy from "@mui/icons-material/SmartToy"
import { Waveform } from "ldrs/react"
import "ldrs/react/Waveform.css"

interface SlowTextProps {
  text: string
  speed?: number
}

const SlowText: React.FC<SlowTextProps> = ({ text, speed = 25 }) => {
  const [displayedText, setDisplayedText] = useState<string>("")
  const idx = useRef<number>(-1)

  useEffect(() => {
    function tick(): void {
      idx.current++
      setDisplayedText((prev: string) => prev + text[idx.current])
    }

    if (idx.current < text.length - 1) {
      const addChar = setInterval(tick, speed)
      return () => clearInterval(addChar)
    }
  }, [displayedText, speed, text])

  return <span>{displayedText}</span>
}

interface MessageProps {
  content: string
  aiMessage: boolean
  animate: boolean
  loading: boolean
}

const Message: React.FC<MessageProps> = ({
  content,
  aiMessage,
  animate,
  loading,
}) => {
  return (
    <div
      className={`flex w-full items-start gap-2 px-4 py-6 sm:px-8 md:px-16 md:py-[30px] lg:px-[120px] ${aiMessage ? "bg-[rgb(247,247,248)]" : ""}`}
    >
      <div className="flex h-[35px] w-[35px] flex-shrink-0 items-center justify-center">
        {aiMessage ? (
          <SmartToy sx={{ fontSize: 24 }} />
        ) : (
          <Person sx={{ fontSize: 24 }} />
        )}
      </div>
      <div className="ml-2 min-w-0 flex-1 break-words">
        {loading ? (
          <div style={{ opacity: 0.5 }}>
            <Waveform size="20" stroke="3.5" speed="1" color="#049FD9" />
          </div>
        ) : animate ? (
          <SlowText speed={20} text={content} />
        ) : (
          content
        )}
      </div>
    </div>
  )
}

export default Message
