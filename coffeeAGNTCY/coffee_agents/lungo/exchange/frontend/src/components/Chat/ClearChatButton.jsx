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

import React from 'react';
import { LOCAL_STORAGE_KEY } from './Messages';
import { v4 as uuid } from 'uuid';
import { MdDeleteSweep } from 'react-icons/md';
import { Role } from '../../utils/const.js';
import './styles/Chat.css';

const ClearChatButton = ({ setMessages }) => {
    const clearChat = () => {
        const initialMessage = {
            role: Role.ASSISTANT,
            content: 'Hi, you are having a conversation with the supervisor. How can I help you?',
            id: uuid(),
            animate: true,
        };
        setMessages([initialMessage]);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify([initialMessage]));
    };

    return (
        <button onClick={clearChat} className="clear-chat-button" title="Clear Chat">
            <MdDeleteSweep size={20} />
        </button>
    );
};

export default ClearChatButton;