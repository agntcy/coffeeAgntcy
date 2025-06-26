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
import './styles/Chat.css';
import MessageInput from './MessageInput';
import Messages, { LOCAL_STORAGE_KEY } from './Messages';
import ClearChatButton from "./ClearChatButton.jsx";
import { Role } from '../../utils/const.js';

const Chat = ({ messages, setMessages, setButtonClicked, setAiReplied }) => {
    const [headerVisible, setHeaderVisible] = useState(true);

    const handleScroll = (e) => {
        const { scrollTop } = e.target;
        setHeaderVisible(scrollTop === 0); // Show header when at the top

    };

    useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
    }, [messages]);

    useEffect(() => {
    const updated = messages.map((msg) =>
        msg.role === Role.ASSISTANT && msg.animate ? { ...msg, animate: false } : msg
    );

    const needsUpdate = JSON.stringify(messages) !== JSON.stringify(updated);
    if (needsUpdate) {
      setMessages(updated);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
    }
    }, []);

    return (
        <div className="chat_container">
            {/*<div*/}
            {/*    className={`chat_header ${headerVisible ? '' : 'hidden'}`}*/}
            {/*>*/}
            {/*    Conversation with Buyer Agent:*/}
            {/*</div>*/}
            <div className={`clear_chat_button_container ${headerVisible ? '' : 'hidden'}`}>
                <ClearChatButton setMessages={setMessages} />
            </div>
            <div className="messages_container" onScroll={handleScroll}>
                <Messages messages={messages} setMessages={setMessages} />
            </div>
            <div className="message_input_container">
                <MessageInput
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                />
            </div>
        </div>
    );
};

export default Chat;
