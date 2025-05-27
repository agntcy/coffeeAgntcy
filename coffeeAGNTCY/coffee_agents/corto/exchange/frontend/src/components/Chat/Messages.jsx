import React, {useEffect} from 'react'
import Message from './Message'

export const LOCAL_STORAGE_KEY = "chat_messages";

function Messages({ messages }) {

  return (
    <div className='chat_messages_container'>
      {messages.map((msg) => (
        <Message
          key={msg.id}
          content={msg.content}
          aiMessage={msg.role === 'assistant'}
          animate={msg.animate}
        />
      ))}
    </div>
  );
}

export default Messages
