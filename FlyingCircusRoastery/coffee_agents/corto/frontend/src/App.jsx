import React, { useState, useEffect } from 'react';
import Graph from './components/MainArea/Graph';
import Chat from './components/Chat/Chat';
import './App.css';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from './components/Chat/Messages';

const App = () => {
    const [messages, setMessages] = useState(() => {
        const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
        return saved
            ? JSON.parse(saved)
            : [{ role: 'assistant', content: 'Hi! How can I assist you?', id: uuid(), animate: false }];
    });

    const [buttonClicked, setButtonClicked] = useState(false);

    useEffect(() => {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(messages));
    }, [messages]);

    return (
        <div className="app-container">
            <div className="sidebar">
                <Chat
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                />
            </div>
            <div className="main-area">
                <header>Buyers Exchange</header>
                <div className="main-panel">
                    <Graph buttonClicked={buttonClicked} setButtonClicked={setButtonClicked} />
                </div>
            </div>
        </div>
    );
};

export default App;