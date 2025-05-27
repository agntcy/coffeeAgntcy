import React, { useState, useEffect } from 'react';
import './Chat.css';
import MessageInput from './MessageInput';
import Messages, { LOCAL_STORAGE_KEY } from './Messages';
import { v4 as uuid } from 'uuid';

import logoSrc from '../../assets/agntcy_coffee.png'; 

const ChatLogo = () => {
  return (
    <div className="chat_logo_container">
      <img src={logoSrc} alt="Agency Coffee Logo" className="chat_logo_img" />
    </div>
  );
};

const Chat = () => {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
    return saved
      ? JSON.parse(saved)
      : [{ role: 'assistant', content: 'Hi! How can I help you?', id: uuid(), animate: false }];
  });

  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    // After first render, remove animation flags from AI messages
    const updated = messages.map((msg) =>
      msg.role === 'assistant' && msg.animate ? { ...msg, animate: false } : msg
    );

    // Save only if there was a change
    const needsUpdate = JSON.stringify(messages) !== JSON.stringify(updated);
    if (needsUpdate) {
      setMessages(updated);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
    }
  }, []); // run once on mount

  return (
    <div className="chat_container">
      <ChatLogo />
      <Messages messages={messages} />
      <MessageInput messages={messages} setMessages={setMessages} />
    </div>
  );
};

export default Chat;
