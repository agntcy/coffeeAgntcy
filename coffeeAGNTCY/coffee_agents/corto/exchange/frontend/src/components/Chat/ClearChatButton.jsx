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
import React from 'react';
import { css } from '@emotion/react';
import { LOCAL_STORAGE_KEY } from './Messages';
import { v4 as uuid } from 'uuid';
import { MdDeleteSweep } from 'react-icons/md';
import { Role } from '../../utils/const.js';

const buttonStyle = css`
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4d4c4c; /* Neutral color matching the UI */
  padding: 0.2em;
  opacity: 0.85;
  border-radius: 5px;
  transition: background-color 0.3s ease, color 0.3s ease;

  &:hover {
    background-color: rgba(10, 96, 255, 0.1); /* Subtle hover effect */
    color: #0A60FF; /* Primary color on hover */
  }
`;

const ClearChatButton = ({ setMessages }) => {
    const clearChat = () => {
        const initialMessage = {
            role: Role.ASSISTANT,
            content: 'Hi! How can I assist you?',
            id: uuid(),
            animate: true,
        };
        setMessages([initialMessage]);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify([initialMessage]));
    };

    return (
        <button onClick={clearChat} css={buttonStyle} title="Clear Chat">
            <MdDeleteSweep size={20} />
        </button>
    );
};

export default ClearChatButton;