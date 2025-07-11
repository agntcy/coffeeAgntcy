/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useState } from 'react';
import { IoSendSharp } from 'react-icons/io5';
import { v4 as uuid } from 'uuid';
import axios from 'axios';
import { Role } from '../../utils/const.js';
import './styles/Messages.css';

const DEFAULT_EXCHANGE_APP_API_URL = 'http://0.0.0.0:8000';

function MessageInput({ messages, setMessages, setButtonClicked, setAiReplied }) {
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(false);

    const processMessage = async () => {
        if (!content.trim()) return;

        const userMessage = {
            role: Role.USER,
            content: content,
            id: uuid(),
            animate: false,
        };

        const loadingMessage = {
            role: 'assistant',
            content: "Loading...",
            id: uuid(),
            animate: false,
            loading: true,
        };

        const updatedMessages = [...messages, userMessage, loadingMessage];
        setLoading(true);

        setMessages(updatedMessages);
        setContent('');
        setButtonClicked(true);

        try {
            const apiUrl = import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL;
            const resp = await axios.post(`${apiUrl}/agent/prompt`, {
                prompt: content,
            });

            const aiReply = {
                role: 'assistant',
                content: resp.data?.response || "No content received.",
                id: uuid(),
                animate: true,
            };

            setMessages([...messages, userMessage, aiReply]);
        } catch (error) {
            console.error("Error while sending prompt to the server:", error);

            const errorReply = {
                role: 'assistant',
                content: error.response?.data?.detail || "Error from server.",
                id: uuid(),
                animate: true,
            };

            setMessages([...messages, userMessage, errorReply]);
        } finally {
            setLoading(false);
            setAiReplied(true);
        }
    };

    const handleSendMessage = () => {
        if (content.trim().length > 0) {
            processMessage();
        }
    };

    const handleKeyPressed = (event) => {
        if ((event.code === 'Enter' || event.code === 'NumpadEnter') && content.trim().length > 0) {
            processMessage();
        }
    };

    return (
        <div className="message-input-container">
            <input
                className="message-input"
                placeholder="Enter your prompt..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                onKeyDown={handleKeyPressed}
                disabled={loading}
            />
            <div
                className={`icon-container ${!content.trim() || loading ? 'disabled' : ''}`}
                onClick={!content.trim() || loading ? null : handleSendMessage}
            >
                <IoSendSharp color="#00BCEB" />
            </div>
        </div>
    );
}

export default MessageInput;