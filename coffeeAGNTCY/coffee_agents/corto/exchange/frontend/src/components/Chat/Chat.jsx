import React, { useState, useEffect } from 'react';
import './Chat.css';
import MessageInput from './MessageInput';
import Messages, { LOCAL_STORAGE_KEY } from './Messages';

import logoSrc from '../../assets/coffee_agntcy.png';

const ChatLogo = () => {
  return (
    <div className="chat_logo_container">
      <img src={logoSrc} alt="Agency Coffee Logo" className="chat_logo_img" />
    </div>
  );
};

const Chat = ({ messages, setMessages, setButtonClicked }) => {
  useEffect(() => {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    const updated = messages.map((msg) =>
        msg.role === 'assistant' && msg.animate ? { ...msg, animate: false } : msg
    );

    const needsUpdate = JSON.stringify(messages) !== JSON.stringify(updated);
    if (needsUpdate) {
      setMessages(updated);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
    }
  }, []);

  return (
      <div className="chat_container">
        <ChatLogo />
        <Messages messages={messages} />
        <MessageInput
            messages={messages}
            setMessages={setMessages}
            setButtonClicked={setButtonClicked}
        />
      </div>
  );
};

export default Chat;
