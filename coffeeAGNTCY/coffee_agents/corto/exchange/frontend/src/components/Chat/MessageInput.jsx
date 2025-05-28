import React, { useState } from 'react';
import { IoSendSharp } from 'react-icons/io5';
import { v4 as uuid } from 'uuid';
import axios from 'axios';
import './Chat.css';

function MessageInput({ messages, setMessages, setButtonClicked }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  const processMessage = async () => {
    if (!content.trim()) return;

    const userMessage = {
      role: 'user',
      content: content,
      id: uuid(),
      animate: false,
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setContent('');
    setLoading(true);
    setButtonClicked(true);

    try {
      const apiUrl = import.meta.env.VITE_EXCHANGE_APP_API_URL || "http://0.0.0.0:8000";
      console.log("API URL:", apiUrl);
      const resp = await axios.post(`${apiUrl}/agent/prompt`, {
        prompt: content,
      });

      const aiReply = {
        role: 'assistant',
        content: resp.data?.response || "No content received.",
        id: uuid(),
        animate: true,
      };

      setMessages([...updatedMessages, aiReply]);
    } catch (error) {
      console.error("Error while sending prompt to the server:", error);

      const errorReply = {
        role: 'assistant',
        content: error.response?.data?.detail || "Error from server.",
        id: uuid(),
        animate: true,
      };

      setMessages([...updatedMessages, errorReply]);
    } finally {
      setLoading(false);
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
      <div className='message_input_container'>
        <input
            className='message_input'
            placeholder='Enter your prompt...'
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyPressed}
            disabled={loading}
        />
        <div className='message_icon_container' onClick={handleSendMessage}>
          <IoSendSharp color='#00BCEB' />
        </div>
      </div>
  );
}

export default MessageInput;