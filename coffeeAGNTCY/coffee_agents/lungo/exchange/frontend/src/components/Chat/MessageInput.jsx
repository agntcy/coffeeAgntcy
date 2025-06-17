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

/** @jsxImportSource @emotion/react */
import React, { useState } from 'react';
import { IoSendSharp } from 'react-icons/io5';
import { v4 as uuid } from 'uuid';
import axios from 'axios';
import { css } from '@emotion/react';
import { Role } from '../../utils/const.js';

const DEFAULT_EXCHANGE_APP_API_URL = 'http://0.0.0.0:8000';

const containerStyle = css`
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
`;

const inputStyle = css`
  width: 650px;
  border: 1px solid #ccc;
  border-radius: 8px;
  height: 40px;
  outline: none;
  font-size: 14px;
  padding: 0 10px;
  font-family: inherit;
`;

const iconContainerStyle = (disabled) => css`
  position: absolute;
  right: 17.5px;
  top: 50%;
  transform: translateY(-50%);
  cursor: ${disabled ? 'text' : 'pointer'};
  opacity: ${disabled ? 0.5 : 1};
`;

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

            // Replace the loading message with the actual response
            setMessages([...messages, userMessage, aiReply]);
        } catch (error) {
            console.error("Error while sending prompt to the server:", error);

            const errorReply = {
                role: 'assistant',
                content: error.response?.data?.detail || "Error from server.",
                id: uuid(),
                animate: true,
            };

            // Replace the loading message with the error message
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
        <div css={containerStyle}>
            <input
                css={inputStyle}
                placeholder="Enter your prompt..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                onKeyDown={handleKeyPressed}
                disabled={loading}
            />
            <div
                css={iconContainerStyle(!content.trim() || loading)}
                onClick={!content.trim() || loading ? null : handleSendMessage}
            >
                <IoSendSharp color="#00BCEB" />
            </div>
        </div>
    );
}

export default MessageInput;