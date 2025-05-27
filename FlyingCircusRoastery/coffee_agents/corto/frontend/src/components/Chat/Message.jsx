import React, { useEffect, useRef, useState } from 'react';
import { HiUser } from 'react-icons/hi';
import { RiRobot2Fill } from "react-icons/ri";

const SlowText = ({ text, speed = 25 }) => {
  const [displayedText, setDisplayedText] = useState('');
  const idx = useRef(-1);

  useEffect(() => {
    function tick() {
      idx.current++;
      setDisplayedText((prev) => prev + text[idx.current]);
    }

    if (idx.current < text.length - 1) {
      const addChar = setInterval(tick, speed);
      return () => clearInterval(addChar);
    }
  }, [displayedText, speed, text]);

  return <span>{displayedText}</span>;
};

function Message({ content, aiMessage, animate }) {
  return (
    <div
      className="message_container"
      style={{ background: aiMessage ? 'rgb(247, 247, 248)' : 'white' }}
    >
      <div className="message_avatar_container">
        {aiMessage ? <RiRobot2Fill color="#049FD9" /> : <HiUser />}
      </div>
      <p className="message_text">
        {animate ? <SlowText speed={20} text={content} /> : content}
      </p>
    </div>
  );
}

export default Message;
