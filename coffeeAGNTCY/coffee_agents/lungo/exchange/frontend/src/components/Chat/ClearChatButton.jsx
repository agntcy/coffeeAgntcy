/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

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