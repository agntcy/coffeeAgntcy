/** @jsxImportSource @emotion/react */
import React, { useEffect, useRef, useState } from 'react';
import { css } from '@emotion/react';
import { HiUser } from 'react-icons/hi';
import { RiRobot2Fill } from "react-icons/ri";
import { Waveform } from 'ldrs/react';
import 'ldrs/react/Waveform.css';

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

function Message({ content, aiMessage, animate, loading }) {
    return (
        <div css={messageContainerStyle(aiMessage)}>
            <div css={avatarContainerStyle}>
                {aiMessage ? <RiRobot2Fill color="#049FD9" /> : <HiUser />}
            </div>
            <p css={messageTextStyle}>
                {loading ? (
                    <div style={{ opacity: 0.5 }}>
                        <Waveform size="20" stroke="3.5" speed="1" color="#049FD9" />
                    </div>
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