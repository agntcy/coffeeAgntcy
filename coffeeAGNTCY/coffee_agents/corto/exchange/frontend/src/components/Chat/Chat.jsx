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

import React, { useEffect } from 'react';
import './Chat.css';
import MessageInput from './MessageInput';
import Messages, { LOCAL_STORAGE_KEY } from './Messages';
import ClearChatButton from "./ClearChatButton.jsx";
import { Role } from '../../utils/const.js';

const Chat = ({ messages, setMessages, setButtonClicked }) => {
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
        <div className="clear_chat_button_container">
            <ClearChatButton setMessages={setMessages} />
        </div>
          <div  className="messages_container">
              <Messages messages={messages} setMessages={setMessages} />
          </div>
        <div className="message_input_container">
            <MessageInput
                          messages={messages}
                          setMessages={setMessages}
                          setButtonClicked={setButtonClicked}
            />
        </div>
      </div>
  );
};

export default Chat;
