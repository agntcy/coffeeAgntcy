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

import React, { useState, useEffect } from 'react';
import Graph from './components/MainArea/Graph';
import Chat from './components/Chat/Chat';
import './App.css';
import { v4 as uuid } from 'uuid';
import { LOCAL_STORAGE_KEY } from './components/Chat/Messages';
import ChatLogo from './components/Chat/ChatLogo';
import CodePopUp from "./components/MainArea/CodePopUp.jsx"; // Import the ChatLogo component

const App = () => {
    const [aiReplied, setAiReplied] = useState(false);
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
                <ChatLogo />
                <Chat
                    messages={messages}
                    setMessages={setMessages}
                    setButtonClicked={setButtonClicked}
                    setAiReplied={setAiReplied}
                />
            </div>
            <div className="main-area">
                <header className="header">
                    Grader Conversation
                </header>
                <div className="code_popup_container">
                    <CodePopUp/>
                </div>
                <div className="graph_container">
                    <Graph buttonClicked={buttonClicked}
                           setButtonClicked={setButtonClicked}
                           aiReplied={aiReplied}
                           setAiReplied={setAiReplied}
                    />
                </div>
            </div>
        </div>
    );
};

export default App;
