/**
 * Copyright 2025 Cisco Systems, Inc. and its affiliates
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef, useState } from 'react';
import { HiUser } from 'react-icons/hi';
import { RiRobot2Fill } from "react-icons/ri";
import { Waveform } from 'ldrs/react';
import 'ldrs/react/Waveform.css';
import './styles/Messages.css';

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

function Message({ content, aiMessage, animate, loading }) {
    return (
        <div className={`message-container ${aiMessage ? 'ai-message' : ''}`}>
            <div className="avatar-container">
                {aiMessage ? <RiRobot2Fill color="#049FD9" /> : <HiUser />}
            </div>
            <div className="message-text">
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
    );
}

export default Message;