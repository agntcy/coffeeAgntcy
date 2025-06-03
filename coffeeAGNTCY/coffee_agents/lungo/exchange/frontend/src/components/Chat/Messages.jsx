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

import React, { useEffect, useRef } from 'react';
import Message from './Message';

export const LOCAL_STORAGE_KEY = "chat_messages";

function Messages({ messages }) {
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // Scroll to the bottom whenever messages change
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div>
            {messages.map((msg) => (
                <Message
                    key={msg.id}
                    content={msg.content}
                    aiMessage={msg.role === 'assistant'}
                    animate={msg.animate}
                    loading={msg.loading} // Remove loading from individual messages
                />
            ))}
            {/* Invisible div to ensure scrolling to the bottom */}
            <div ref={messagesEndRef} />
        </div>
    );
}

export default Messages;