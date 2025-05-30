/** @jsxImportSource @emotion/react */
import React, { useEffect, useRef, useState } from 'react';
import { css } from '@emotion/react';
import { HiUser } from 'react-icons/hi';
import { RiRobot2Fill } from "react-icons/ri";
import { AiOutlineLoading3Quarters } from "react-icons/ai"; // Loading spinner icon

const SlowText = ({ text, speed = 25 }) => {
    const [displayedText, setDisplayedText] = useState('');
    const idx = useRef(-1);

    useEffect(() => {
        function tick() {
            idx.current++;
            setDisplayedText((prev) => prev + text[idx.current]);
        }

        if (idx.current < text.length - 1) {
            const addChar = setInterval(tick, speed);
            return () => clearInterval(addChar);
        }
    }, [displayedText, speed, text]);

    return <span>{displayedText}</span>;
};

const messageContainerStyle = (aiMessage) => css`
  display: flex;
  justify-content: center;
  padding: 30px 0;
  background: ${aiMessage ? 'rgb(247, 247, 248)' : 'white'};
`;

const avatarContainerStyle = css`
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const messageTextStyle = css`
  width: 80%;
  padding: 0;
  margin: 8px;
  overflow-wrap: break-word;
`;

const loadingIconStyle = css`
  font-size: 24px;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

function Message({ content, aiMessage, animate, loading }) {
    return (
        <div css={messageContainerStyle(aiMessage)}>
            <div css={avatarContainerStyle}>
                {aiMessage ? <RiRobot2Fill color="#049FD9" /> : <HiUser />}
            </div>
            <p css={messageTextStyle}>
                {loading ? (
                    <AiOutlineLoading3Quarters css={loadingIconStyle} />
                ) : animate ? (
                    <SlowText speed={20} text={content} />
                ) : (
                    content
                )}
            </p>
        </div>
    );
}

export default Message;