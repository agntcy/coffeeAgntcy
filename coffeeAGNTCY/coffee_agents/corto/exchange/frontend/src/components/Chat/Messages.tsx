/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useEffect, useRef } from 'react';
import { Message as MessageType } from '@/types/Message';
import Message from './Message';

export const LOCAL_STORAGE_KEY = "chat_messages";

interface MessagesProps {
    messages: MessageType[];
}

const Messages: React.FC<MessagesProps> = ({ messages }) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div>
            {messages.map((msg: MessageType) => (
                <Message
                    key={msg.id}
                    content={msg.content}
                    aiMessage={msg.role === 'assistant'}
                    animate={msg.animate}
                    loading={false} 
                />
            ))}
           
            <div ref={messagesEndRef} />
        </div>
    );
};

export default Messages;
